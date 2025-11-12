# Domain 層規劃總結

## 已完成的工作

### 1. 創建組織規範文檔

**檔案：** `Domain 層組織規範.md`

說明 Domain 層的組織原則、目錄結構規範、實體組織規範等，包括：
- 按聚合根組織的原則
- 簡單聚合 vs 複雜聚合的組織方式
- 命名規範
- 最佳實踐

### 2. 優化現有 Cart 聚合

**檔案：** `core/domain/cart.py`

優化內容：
- ✅ 將 `CartItem` 標記為不可變（`frozen=True`），符合值對象特性
- ✅ 更新 `add_item` 方法，正確處理不可變對象
- ✅ 添加文檔字符串，說明實體職責
- ✅ 保持向後兼容，不影響現有導入

### 3. 創建 Domain 層入口文件

**檔案：** `core/domain/__init__.py`

統一導出所有聚合根和主要實體，方便其他層使用：

```python
from app.core.domain.cart import Cart, CartItem

__all__ = ["Cart", "CartItem"]
```

### 4. 創建複雜聚合示例

**目錄：** `core/domain/order/`

創建了 Order 聚合作為複雜聚合的示例，展示子目錄組織方式：

```
order/
├── __init__.py          # 導出主要實體
├── order.py            # Order 聚合根
├── order_item.py       # OrderItem 實體
├── order_status.py     # OrderStatus 枚舉
└── shipping_address.py # ShippingAddress 值對象
```

### 5. 創建遷移指南

**檔案：** `Domain 層遷移指南.md`

說明如何從簡單聚合遷移到複雜聚合，包括：
- 何時需要遷移
- 遷移步驟
- 注意事項
- 遷移檢查清單
- 回滾策略

---

## 當前 Domain 層結構

```
core/domain/
├── __init__.py              # 統一導出
├── cart.py                  # Cart 聚合（簡單聚合，單一檔案）
└── order/                   # Order 聚合（複雜聚合，子目錄）
    ├── __init__.py
    ├── order.py
    ├── order_item.py
    ├── order_status.py
    └── shipping_address.py
```

---

## 組織原則總結

### 簡單聚合（單一檔案）

**適用條件：**
- 1-2 個實體/值對象
- 業務邏輯簡單（< 10 個方法）
- 檔案長度 < 300 行

**範例：** `cart.py`

### 複雜聚合（子目錄）

**適用條件：**
- 3+ 個實體/值對象
- 業務邏輯複雜（10+ 個方法）
- 需要領域服務、枚舉等
- 檔案長度 > 300 行

**範例：** `order/` 目錄

---

## 設計要點

### 1. 值對象（Value Object）

- ✅ 使用 `@dataclass(frozen=True)` 標記為不可變
- ✅ 不包含業務標識符（ID）
- ✅ 通過值比較相等性

**範例：** `CartItem`、`ShippingAddress`

### 2. 實體（Entity）

- ✅ 包含業務標識符（ID）
- ✅ 可變（mutable）
- ✅ 通過 ID 比較相等性

**範例：** `OrderItem`

### 3. 聚合根（Aggregate Root）

- ✅ 是聚合的入口點
- ✅ 負責維護聚合內的不變條件
- ✅ 包含業務邏輯方法

**範例：** `Cart`、`Order`

### 4. 枚舉（Enum）

- ✅ 用於狀態、類型等有限集合
- ✅ 放在獨立檔案中

**範例：** `OrderStatus`

---

## 導入方式

### 方式 1：直接從聚合模組導入（推薦）

```python
# 簡單聚合
from app.core.domain.cart import Cart, CartItem

# 複雜聚合
from app.core.domain.order import Order, OrderItem, OrderStatus
```

### 方式 2：從 domain 層統一導入（可選）

```python
from app.core.domain import Cart, CartItem, Order, OrderItem
```

---

## 未來擴展建議

### 當 Cart 聚合變複雜時

如果未來 Cart 聚合需要添加：
- 優惠券（Coupon）
- 配送選項（ShippingOption）
- 購物車驗證服務（CartValidator）

可以按以下步驟遷移：

1. 創建 `core/domain/cart/` 目錄
2. 拆分實體到獨立檔案
3. 創建 `__init__.py` 導出主要實體
4. 更新導入（保持向後兼容）

詳細步驟請參考 `Domain 層遷移指南.md`。

---

## 相關文檔

- `Domain 層組織規範.md` - 詳細的組織規範和最佳實踐
- `Domain 層遷移指南.md` - 從簡單聚合遷移到複雜聚合的指南
- `架構說明.md` - 整體架構說明
- `API 層架構設計.md` - API 層設計規範

---

## 總結

Domain 層的規劃遵循以下原則：

1. **按聚合組織**：相關實體放在同一個聚合中
2. **簡單優先**：簡單聚合使用單一檔案，複雜聚合使用子目錄
3. **業務導向**：使用業務術語命名，保持 Domain 層的純粹性
4. **易於擴展**：當聚合變複雜時，可以平滑遷移到子目錄結構
5. **向後兼容**：遷移時盡量保持向後兼容，減少影響範圍

這樣的設計確保了：
- ✅ 程式碼清晰易讀
- ✅ 符合 DDD（Domain-Driven Design）原則
- ✅ 符合 Clean Architecture 原則
- ✅ 易於測試與維護
- ✅ 易於擴展新功能

