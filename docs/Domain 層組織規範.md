# Domain 層組織規範

## 概述

本文檔說明 `core/domain/` 目錄的組織規範，包括實體（Entity）、值對象（Value Object）、領域服務（Domain Service）等的組織方式與命名規範。

---

## 組織原則

### 1. 按聚合根（Aggregate Root）組織

Domain 層按**業務聚合**組織，每個聚合對應一個目錄或模組。

**聚合（Aggregate）**：一組相關的領域對象，以聚合根為入口，共同維護業務不變條件。

### 2. 簡單聚合：單一檔案

當一個聚合只包含少量實體（1-3 個）且邏輯簡單時，可以放在單一檔案中。

**範例：**

```python
# core/domain/cart.py
@dataclass
class CartItem:
    """購物車項目（值對象）"""
    product_id: str
    quantity: int
    unit_price: int

@dataclass
class Cart:
    """購物車（聚合根）"""
    user_id: str
    items: List[CartItem] = field(default_factory=list)
    
    def add_item(self, ...): ...
    def total_amount(self) -> int: ...
```

### 3. 複雜聚合：子目錄組織

當一個聚合包含多個實體、值對象、領域服務或複雜業務邏輯時，使用子目錄組織。

**範例結構：**

```
core/domain/
├── cart/                    # Cart 聚合
│   ├── __init__.py         # 導出聚合根和主要實體
│   ├── cart.py             # Cart 聚合根
│   ├── cart_item.py        # CartItem 值對象
│   └── cart_validator.py   # 領域服務（如需要）
├── order/                   # Order 聚合
│   ├── __init__.py
│   ├── order.py            # Order 聚合根
│   ├── order_item.py       # OrderItem 值對象
│   ├── shipping_address.py # ShippingAddress 值對象
│   └── order_status.py     # OrderStatus 枚舉
└── product/                 # Product 聚合
    ├── __init__.py
    ├── product.py          # Product 聚合根
    └── product_category.py # ProductCategory 值對象
```

---

## 目錄結構規範

### 基本結構

```
core/domain/
├── __init__.py              # 導出所有聚合根（可選）
├── {aggregate}/             # 按聚合組織
│   ├── __init__.py         # 導出該聚合的主要實體
│   ├── {aggregate_root}.py # 聚合根實體
│   ├── {entity}.py         # 其他實體（如需要）
│   ├── {value_object}.py   # 值對象（如需要）
│   └── {domain_service}.py # 領域服務（如需要）
```

### 命名規範

#### 聚合目錄命名

- **單數形式**：`cart/`、`order/`、`product/`
- **小寫字母**：使用小寫字母和底線
- **業務導向**：使用業務術語，而非技術術語

#### 檔案命名

- **聚合根**：`{aggregate}.py`（如 `cart.py`、`order.py`）
- **實體**：`{entity_name}.py`（如 `cart_item.py`、`order_item.py`）
- **值對象**：`{value_object_name}.py`（如 `shipping_address.py`、`money.py`）
- **領域服務**：`{service_name}.py`（如 `cart_validator.py`、`price_calculator.py`）
- **枚舉**：`{enum_name}.py`（如 `order_status.py`、`payment_status.py`）

---

## 實體組織規範

### 1. 聚合根（Aggregate Root）

**特徵：**
- 是聚合的入口點
- 負責維護聚合內的不變條件
- 包含業務邏輯方法
- 通常對應資料庫中的主表

**範例：**

```python
# core/domain/cart/cart.py
@dataclass
class Cart:
    """購物車聚合根"""
    user_id: str
    items: List[CartItem] = field(default_factory=list)
    
    def add_item(self, product_id: str, unit_price: int, quantity: int = 1) -> None:
        """添加商品到購物車"""
        # 業務邏輯：驗證、更新等
        ...
    
    def total_amount(self) -> int:
        """計算總金額"""
        return sum(item.unit_price * item.quantity for item in self.items)
```

### 2. 值對象（Value Object）

**特徵：**
- 不可變（immutable）
- 通過值比較相等性
- 不包含業務標識符（ID）
- 通常作為聚合根的屬性

**範例：**

```python
# core/domain/cart/cart_item.py
@dataclass(frozen=True)  # 不可變
class CartItem:
    """購物車項目（值對象）"""
    product_id: str
    quantity: int
    unit_price: int
```

### 3. 實體（Entity）

**特徵：**
- 包含業務標識符（ID）
- 可變（mutable）
- 通過 ID 比較相等性
- 通常對應資料庫中的獨立表

**範例：**

```python
# core/domain/order/order_item.py
@dataclass
class OrderItem:
    """訂單項目（實體）"""
    item_id: str  # 業務標識符
    product_id: str
    quantity: int
    unit_price: int
```

### 4. 領域服務（Domain Service）

**特徵：**
- 包含不屬於單一實體的業務邏輯
- 無狀態（stateless）
- 操作多個實體或值對象

**範例：**

```python
# core/domain/cart/cart_validator.py
class CartValidator:
    """購物車驗證領域服務"""
    
    @staticmethod
    def validate_cart_for_checkout(cart: Cart) -> None:
        """驗證購物車是否可以結帳"""
        if not cart.items:
            raise ValueError("購物車為空")
        if cart.total_amount() <= 0:
            raise ValueError("購物車總金額無效")
        # 其他驗證邏輯...
```

---

## 遷移策略

### 從單一檔案遷移到子目錄

當聚合變得複雜時，可以按以下步驟遷移：

#### 步驟 1：創建子目錄結構

```
core/domain/
├── cart/
│   ├── __init__.py
│   ├── cart.py
│   └── cart_item.py
```

#### 步驟 2：拆分實體

將 `cart.py` 中的實體拆分到對應檔案：

```python
# core/domain/cart/cart_item.py
@dataclass(frozen=True)
class CartItem:
    product_id: str
    quantity: int
    unit_price: int

# core/domain/cart/cart.py
from app.core.domain.cart.cart_item import CartItem

@dataclass
class Cart:
    user_id: str
    items: List[CartItem] = field(default_factory=list)
    # ...
```

#### 步驟 3：更新 `__init__.py`

```python
# core/domain/cart/__init__.py
from app.core.domain.cart.cart import Cart
from app.core.domain.cart.cart_item import CartItem

__all__ = ["Cart", "CartItem"]
```

#### 步驟 4：更新導入

更新所有引用該聚合的檔案：

```python
# 舊的導入方式
from app.core.domain.cart import Cart, CartItem

# 新的導入方式（保持兼容）
from app.core.domain.cart import Cart, CartItem
```

---

## 完整範例

### 範例 1：簡單聚合（單一檔案）

```python
# core/domain/cart.py
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class CartItem:
    """購物車項目（值對象）"""
    product_id: str
    quantity: int
    unit_price: int

@dataclass
class Cart:
    """購物車（聚合根）"""
    user_id: str
    items: List[CartItem] = field(default_factory=list)
    
    def add_item(self, product_id: str, unit_price: int, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        
        # 查找現有項目
        for item in self.items:
            if item.product_id == product_id:
                # 創建新的不可變對象
                new_item = CartItem(
                    product_id=item.product_id,
                    quantity=item.quantity + quantity,
                    unit_price=item.unit_price
                )
                self.items = [new_item if i.product_id == product_id else i 
                             for i in self.items]
                return
        
        # 添加新項目
        self.items.append(
            CartItem(product_id=product_id, quantity=quantity, unit_price=unit_price)
        )
    
    def total_amount(self) -> int:
        return sum(item.unit_price * item.quantity for item in self.items)
```

### 範例 2：複雜聚合（子目錄）

```
core/domain/order/
├── __init__.py
├── order.py
├── order_item.py
├── shipping_address.py
├── order_status.py
└── order_validator.py
```

```python
# core/domain/order/__init__.py
from app.core.domain.order.order import Order
from app.core.domain.order.order_item import OrderItem
from app.core.domain.order.shipping_address import ShippingAddress
from app.core.domain.order.order_status import OrderStatus

__all__ = ["Order", "OrderItem", "ShippingAddress", "OrderStatus"]

# core/domain/order/order.py
from dataclasses import dataclass, field
from typing import List
from app.core.domain.order.order_item import OrderItem
from app.core.domain.order.shipping_address import ShippingAddress
from app.core.domain.order.order_status import OrderStatus

@dataclass
class Order:
    """訂單聚合根"""
    order_id: str
    user_id: str
    items: List[OrderItem] = field(default_factory=list)
    shipping_address: ShippingAddress | None = None
    status: OrderStatus = OrderStatus.PENDING
    
    def add_item(self, product_id: str, quantity: int, unit_price: int) -> None:
        # 業務邏輯...
        ...
    
    def confirm(self) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("只能確認待處理的訂單")
        self.status = OrderStatus.CONFIRMED

# core/domain/order/order_item.py
@dataclass
class OrderItem:
    """訂單項目（實體）"""
    item_id: str
    product_id: str
    quantity: int
    unit_price: int

# core/domain/order/shipping_address.py
@dataclass(frozen=True)
class ShippingAddress:
    """配送地址（值對象）"""
    street: str
    city: str
    postal_code: str
    country: str

# core/domain/order/order_status.py
from enum import Enum

class OrderStatus(Enum):
    """訂單狀態（枚舉）"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

---

## 最佳實踐

### ✅ 應該做的

1. **按業務聚合組織**：相關的實體放在同一個聚合中
2. **聚合根作為入口**：外部只能通過聚合根操作聚合內的實體
3. **值對象不可變**：使用 `@dataclass(frozen=True)` 標記值對象
4. **業務邏輯在實體中**：實體方法包含業務邏輯，而非在 Service 層
5. **保持簡單**：簡單聚合使用單一檔案，複雜聚合使用子目錄
6. **清晰的導入**：通過 `__init__.py` 導出主要實體，保持導入簡潔

### ❌ 不應該做的

1. **不要跨聚合直接引用**：聚合之間通過 ID 或值對象引用
2. **不要在 Domain 層使用技術框架**：不使用 ORM、HTTP client 等
3. **不要包含持久化邏輯**：Domain 層不應該知道如何保存到資料庫
4. **不要過度拆分**：簡單的聚合不需要子目錄
5. **不要在 Domain 層依賴 Service 層**：Domain 層應該是最純粹的業務邏輯

---

## 與其他層的關係

### 與 Service 層

- **依賴方向**：Service 層依賴 Domain 層
- **使用方式**：Service 層操作 Domain 實體，協調多個實體完成用例

### 與 Repository 層

- **依賴方向**：Repository 接口定義在 `core/repositories/`，依賴 Domain 層
- **使用方式**：Repository 接口使用 Domain 實體作為參數和返回值

### 與 Infrastructure 層

- **無直接依賴**：Domain 層不依賴 Infrastructure 層
- **轉換方向**：Infrastructure 層將 ORM 模型轉換為 Domain 實體

---

## 決策樹：選擇組織方式

```
開始
  ↓
聚合包含多少實體？
  ↓
1-2 個實體
  ↓
業務邏輯是否簡單？
  ├─ 是 → 使用單一檔案（如 cart.py）
  └─ 否 → 考慮拆分為子目錄
  ↓
3+ 個實體 或 複雜業務邏輯
  ↓
使用子目錄組織
  ├─ 聚合根：{aggregate}.py
  ├─ 實體：{entity}.py
  ├─ 值對象：{value_object}.py
  └─ 領域服務：{service}.py（如需要）
```

---

## 總結

Domain 層的組織遵循以下原則：

1. **按聚合組織**：相關實體放在同一個聚合中
2. **簡單優先**：簡單聚合使用單一檔案，複雜聚合使用子目錄
3. **業務導向**：使用業務術語命名，而非技術術語
4. **清晰分離**：聚合根、實體、值對象、領域服務清晰分離
5. **易於擴展**：當聚合變複雜時，可以平滑遷移到子目錄結構

這樣的設計確保了：
- ✅ 程式碼清晰易讀
- ✅ 符合 DDD（Domain-Driven Design）原則
- ✅ 易於測試與維護
- ✅ 易於擴展新功能
- ✅ 保持 Domain 層的純粹性

