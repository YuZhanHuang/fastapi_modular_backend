# Domain 層遷移指南

## 概述

本文檔說明如何將簡單聚合（單一檔案）遷移到複雜聚合（子目錄結構），以及遷移過程中的注意事項。

---

## 何時需要遷移？

### 觸發遷移的條件

當聚合滿足以下條件時，建議遷移到子目錄結構：

1. **實體數量增加**：聚合包含 3 個或更多實體/值對象
2. **業務邏輯複雜**：聚合根包含大量業務方法（10+ 個方法）
3. **需要領域服務**：需要獨立的領域服務類別來處理複雜業務邏輯
4. **需要枚舉或常數**：需要定義狀態枚舉、錯誤碼等
5. **檔案過長**：單一檔案超過 300 行

### 當前狀態評估

**Cart 聚合（簡單聚合）**
- ✅ 實體數量：2 個（Cart、CartItem）
- ✅ 業務邏輯：簡單（2 個方法）
- ✅ 檔案長度：約 50 行
- **結論**：當前適合使用單一檔案，無需遷移

**Order 聚合（複雜聚合示例）**
- ⚠️ 實體數量：4 個（Order、OrderItem、ShippingAddress、OrderStatus）
- ⚠️ 業務邏輯：較複雜（多個狀態轉換方法）
- ⚠️ 需要枚舉：OrderStatus
- **結論**：適合使用子目錄結構

---

## 遷移步驟

### 步驟 1：創建子目錄結構

```bash
mkdir -p src/app/core/domain/{aggregate}
```

**範例：**

```bash
mkdir -p src/app/core/domain/order
```

### 步驟 2：拆分實體到獨立檔案

將原檔案中的實體拆分到對應檔案：

#### 2.1 值對象（Value Object）

```python
# core/domain/order/shipping_address.py
@dataclass(frozen=True)
class ShippingAddress:
    """配送地址（值對象）"""
    street: str
    city: str
    postal_code: str
    country: str
```

#### 2.2 實體（Entity）

```python
# core/domain/order/order_item.py
@dataclass
class OrderItem:
    """訂單項目（實體）"""
    item_id: str
    product_id: str
    quantity: int
    unit_price: int
```

#### 2.3 枚舉（Enum）

```python
# core/domain/order/order_status.py
from enum import Enum

class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    # ...
```

#### 2.4 聚合根（Aggregate Root）

```python
# core/domain/order/order.py
from dataclasses import dataclass, field
from typing import List
from app.core.domain.order.order_item import OrderItem
from app.core.domain.order.order_status import OrderStatus
from app.core.domain.order.shipping_address import ShippingAddress

@dataclass
class Order:
    """訂單（聚合根）"""
    order_id: str
    user_id: str
    items: List[OrderItem] = field(default_factory=list)
    shipping_address: ShippingAddress | None = None
    status: OrderStatus = OrderStatus.PENDING
    
    # 業務方法...
```

### 步驟 3：創建 `__init__.py`

```python
# core/domain/order/__init__.py
from app.core.domain.order.order import Order
from app.core.domain.order.order_item import OrderItem
from app.core.domain.order.order_status import OrderStatus
from app.core.domain.order.shipping_address import ShippingAddress

__all__ = [
    "Order",
    "OrderItem",
    "OrderStatus",
    "ShippingAddress",
]
```

### 步驟 4：更新導入（保持向後兼容）

#### 選項 A：保持舊的導入方式（推薦）

不修改現有導入，讓舊的導入方式繼續工作：

```python
# 舊的導入方式仍然有效
from app.core.domain.cart import Cart, CartItem

# 新的導入方式也可用
from app.core.domain.order import Order, OrderItem
```

#### 選項 B：統一使用 `__init__.py` 導入

更新所有導入為統一方式：

```python
# 舊的導入方式
from app.core.domain.cart import Cart

# 新的導入方式
from app.core.domain import Cart
```

**注意**：如果選擇選項 B，需要更新所有引用該聚合的檔案。

### 步驟 5：更新 `core/domain/__init__.py`

```python
# core/domain/__init__.py
from app.core.domain.cart import Cart, CartItem
from app.core.domain.order import Order, OrderItem, OrderStatus, ShippingAddress

__all__ = [
    # Cart 聚合
    "Cart",
    "CartItem",
    # Order 聚合
    "Order",
    "OrderItem",
    "OrderStatus",
    "ShippingAddress",
]
```

### 步驟 6：測試與驗證

1. **運行測試**：確保所有測試通過
2. **檢查導入**：確認所有導入路徑正確
3. **檢查類型提示**：確認類型檢查通過

---

## 實際範例：Cart 聚合遷移

### 當前結構（簡單聚合）

```
core/domain/
└── cart.py  # 包含 Cart 和 CartItem
```

### 遷移後結構（複雜聚合）

假設 Cart 聚合變複雜，需要添加優惠券、配送選項等：

```
core/domain/
└── cart/
    ├── __init__.py
    ├── cart.py              # Cart 聚合根
    ├── cart_item.py         # CartItem 值對象
    ├── coupon.py            # Coupon 值對象（新增）
    └── shipping_option.py  # ShippingOption 值對象（新增）
```

### 遷移步驟

#### 1. 創建目錄結構

```bash
mkdir -p src/app/core/domain/cart
```

#### 2. 拆分實體

```python
# core/domain/cart/cart_item.py
@dataclass(frozen=True)
class CartItem:
    product_id: str
    quantity: int
    unit_price: int

# core/domain/cart/cart.py
from dataclasses import dataclass, field
from typing import List
from app.core.domain.cart.cart_item import CartItem

@dataclass
class Cart:
    user_id: str
    items: List[CartItem] = field(default_factory=list)
    # ...
```

#### 3. 創建 `__init__.py`

```python
# core/domain/cart/__init__.py
from app.core.domain.cart.cart import Cart
from app.core.domain.cart.cart_item import CartItem

__all__ = ["Cart", "CartItem"]
```

#### 4. 保持向後兼容

為了保持向後兼容，可以創建一個符號連結或重新導出：

```python
# core/domain/cart.py（保留，用於向後兼容）
from app.core.domain.cart import Cart, CartItem

# 或者直接重新導出
__all__ = ["Cart", "CartItem"]
```

**或者**：更新所有導入為新路徑（推薦，更清晰）

---

## 注意事項

### 1. 循環依賴

確保聚合之間沒有循環依賴。如果聚合 A 需要引用聚合 B，應該：

- **通過 ID 引用**：只保存 ID，不直接引用實體
- **通過值對象引用**：使用值對象而非實體引用

**範例：**

```python
# ✅ 正確：通過 ID 引用
@dataclass
class Order:
    user_id: str  # 只保存 ID
    # ...

# ❌ 錯誤：直接引用實體（可能造成循環依賴）
@dataclass
class Order:
    user: User  # 直接引用 User 實體
    # ...
```

### 2. 導入路徑

遷移後，導入路徑會發生變化：

```python
# 遷移前
from app.core.domain.cart import Cart

# 遷移後（選項 A：保持舊路徑）
from app.core.domain.cart import Cart  # 仍然有效（如果保留 cart.py）

# 遷移後（選項 B：使用新路徑）
from app.core.domain.cart.cart import Cart
# 或
from app.core.domain.cart import Cart  # 通過 __init__.py
```

### 3. 測試更新

遷移後需要更新測試中的導入：

```python
# 測試檔案
from app.core.domain.cart import Cart, CartItem  # 更新導入路徑
```

### 4. 類型提示

確保類型提示正確：

```python
# Service 層
from app.core.domain.cart import Cart

class CartService:
    def get_cart(self, user_id: str) -> Cart:  # 類型提示仍然有效
        ...
```

---

## 遷移檢查清單

### 遷移前

- [ ] 確認聚合確實需要遷移（滿足觸發條件）
- [ ] 備份當前代碼
- [ ] 運行所有測試，確保當前狀態正常

### 遷移中

- [ ] 創建子目錄結構
- [ ] 拆分實體到獨立檔案
- [ ] 創建 `__init__.py` 並導出主要實體
- [ ] 更新 `core/domain/__init__.py`（如需要）
- [ ] 更新導入路徑（如選擇統一導入方式）

### 遷移後

- [ ] 運行所有測試，確保通過
- [ ] 檢查類型提示，確保正確
- [ ] 檢查導入路徑，確保所有引用正確
- [ ] 更新文檔（如需要）
- [ ] 代碼審查

---

## 回滾策略

如果遷移後發現問題，可以按以下步驟回滾：

### 1. 恢復舊檔案

```bash
git checkout HEAD -- src/app/core/domain/cart.py
```

### 2. 刪除新目錄

```bash
rm -rf src/app/core/domain/cart/
```

### 3. 恢復導入

恢復所有導入為舊路徑。

---

## 總結

遷移從簡單聚合到複雜聚合的關鍵點：

1. **評估需求**：確認是否真的需要遷移
2. **保持兼容**：盡量保持向後兼容，減少影響範圍
3. **逐步遷移**：按步驟進行，每步都測試
4. **文檔更新**：更新相關文檔和註釋
5. **團隊溝通**：通知團隊成員遷移計劃

遵循這些步驟，可以安全、順利地完成遷移。

