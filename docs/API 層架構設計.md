# API 層架構設計

## 概述

本文檔說明 API 層的架構設計原則與組織方式，包括 Schema 定義、轉換邏輯、路由處理等組件的職責與組織規範。

---

## 架構原則

### 1. 職責分離

API 層作為 Interface Adapters，負責：
- **HTTP 請求處理**：解析請求參數、驗證輸入
- **HTTP 回應格式化**：將 Domain Model 轉換為 API Schema
- **錯誤處理**：將業務異常轉換為 HTTP 狀態碼

**不負責：**
- 業務邏輯（應在 `core/services/` 處理）
- 資料存取（應在 `infra/` 處理）

### 2. 依賴方向

```
api/
  ├── *.py             # 路由檔案（依賴下層）
  ├── schemas/         # Schema 定義（純資料結構）
  ├── utils/           # 工具層（依賴 schemas 和 domain）
  └── deps.py          # 依賴注入
```

**依賴關係：**
- 路由檔案 → `schemas/` + `utils/` + `deps.py`
- `utils/` → `schemas/` + `core/domain/`
- `schemas/` → 無依賴（純 Pydantic 模型）

---

## 目錄結構

```
api/
├── deps.py                    # FastAPI 依賴注入函數
├── http_app.py                # FastAPI 應用配置
├── carts.py                   # Cart 路由處理
├── schemas/                   # API Schema 定義
│   ├── __init__.py
│   └── cart.py                # Cart 相關 Schema
│       ├── CartItemOut
│       ├── CartOut
│       └── AddItemIn
└── utils/                     # API 層工具
    └── converters/            # Domain → Schema 轉換器
        ├── __init__.py
        └── cart.py           # Cart 轉換邏輯
            ├── cart_item_out_from_domain()
            └── cart_out_from_domain()
```

---

## Schema 組織規範

### 位置

所有 API Schema 定義在 `api/schemas/` 目錄下，**按資源組織**。

### 命名規範

- **Request Schema**：`{Action}{Resource}In`
  - 範例：`AddItemIn`、`UpdateCartIn`、`DeleteItemIn`
  
- **Response Schema**：`{Resource}Out` 或 `{Resource}{Detail}Out`
  - 範例：`CartOut`、`CartItemOut`、`CartDetailOut`

### Schema 職責

Schema 類別**只負責資料結構定義與驗證**，不包含：
- ❌ 轉換邏輯
- ❌ 業務邏輯
- ❌ 複雜計算

**範例：**

```python
# api/schemas/cart.py
class CartOut(BaseModel):
    """購物車回應 Schema"""
    user_id: str
    items: List[CartItemOut]
    total: int
    # ✅ 只定義結構，不包含轉換邏輯
```

---

## 轉換邏輯組織規範

### 位置

Domain Model 到 API Schema 的轉換邏輯放在 `api/utils/converters/` 目錄下，**按資源分檔**。

### 命名規範

轉換函數命名格式：`{schema}_from_domain()`

**範例：**
- `cart_out_from_domain(cart: Cart) -> CartOut`
- `cart_item_out_from_domain(item: CartItem) -> CartItemOut`

### 轉換器職責

轉換器負責：
- ✅ Domain Model → API Schema 的轉換
- ✅ 資料格式轉換（如日期格式、金額單位等）
- ✅ 可選欄位的處理

**不負責：**
- ❌ 業務邏輯計算
- ❌ 資料驗證（應在 Schema 層處理）

### 為什麼選擇獨立轉換器？

**優點：**
1. **職責分離**：轉換邏輯獨立，符合單一職責原則
2. **高度重用**：多個路由、CLI、Worker 都可以使用
3. **易於測試**：轉換邏輯可以完全獨立測試
4. **易於維護**：所有轉換邏輯集中管理
5. **靈活性高**：可以處理複雜的轉換邏輯（多個來源、條件轉換等）
6. **不污染 Schema**：Pydantic 模型保持純粹，只負責驗證

**與其他方案的比較：**

| 方案 | 優點 | 缺點 |
|------|------|------|
| **A. 路由中轉換** | 簡單直觀 | 重複代碼、職責混雜、難以測試 |
| **B. Schema 類別方法** | 封裝良好、易於重用 | Schema 變重、違反單一職責 |
| **C. 獨立轉換器** ✅ | 職責分離、高度重用、易於測試 | 額外抽象層 |

**範例：**

```python
# api/utils/converters/cart.py
def cart_out_from_domain(cart: Cart) -> CartOut:
    """將 Domain Cart 轉換為 API CartOut"""
    return CartOut(
        user_id=cart.user_id,
        items=[cart_item_out_from_domain(item) for item in cart.items],
        total=cart.total_amount(),
    )
```

---

## 路由層規範

### 職責

路由函數負責：
- ✅ HTTP 請求處理
- ✅ 參數驗證（透過 Pydantic Schema）
- ✅ 呼叫 Service 層
- ✅ 錯誤處理與 HTTP 狀態碼轉換
- ✅ 使用轉換器將 Domain Model 轉換為 Response Schema

**不負責：**
- ❌ 業務邏輯（委託給 Service）
- ❌ 資料轉換邏輯（委託給 Converter）
- ❌ 資料結構定義（在 Schema 層）

### 範例

```python
# api/carts.py
from app.api.schemas.cart import CartOut, AddItemIn
from app.api.utils.converters.cart import cart_out_from_domain

@router.get("/cart", response_model=CartOut)
def get_cart(
    user_id: str,
    service: CartService = Depends(get_cart_service),
):
    cart = service.get_cart(user_id)
    return cart_out_from_domain(cart)  # 使用轉換器
```

---

## 完整流程範例

### 請求流程

```
HTTP 請求
  ↓
路由函數 (api/carts.py)
  ↓
Pydantic Schema 驗證 (api/schemas/cart.py)
  ↓
呼叫 Service (core/services/cart_service.py)
  ↓
Service 返回 Domain Model (core/domain/cart.py)
  ↓
轉換器轉換 (api/utils/converters/cart.py)
  ↓
返回 API Schema (api/schemas/cart.py)
  ↓
FastAPI 序列化為 JSON
```

### 程式碼流程

```python
# 1. HTTP 請求進入路由
@router.post("/cart/items", response_model=CartOut)
def add_item(
    user_id: str,
    body: AddItemIn,  # ← Pydantic 自動驗證
    service: CartService = Depends(get_cart_service),
):
    # 2. 呼叫 Service（業務邏輯層）
    cart = service.add_item(
        user_id=user_id,
        product_id=body.product_id,
        unit_price=body.unit_price,
        quantity=body.quantity,
    )
    
    # 3. 使用轉換器轉換 Domain Model → API Schema
    return cart_out_from_domain(cart)
```

---

## 新增資源的步驟

當需要新增新的 API 資源時，按照以下步驟：

### 1. 定義 Schema

```python
# api/schemas/order.py
class OrderOut(BaseModel):
    order_id: str
    user_id: str
    total: int
    # ...
```

### 2. 實作轉換器

```python
# api/utils/converters/order.py
def order_out_from_domain(order: Order) -> OrderOut:
    return OrderOut(
        order_id=order.order_id,
        user_id=order.user_id,
        total=order.total_amount(),
    )
```

### 3. 定義路由

```python
# api/orders.py
from app.api.schemas.order import OrderOut
from app.api.utils.converters.order import order_out_from_domain

@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str, service: OrderService = Depends(get_order_service)):
    order = service.get_order(order_id)
    return order_out_from_domain(order)
```

---

## 最佳實踐

### ✅ 應該做的

1. **Schema 保持純粹**：只定義資料結構，不包含轉換邏輯
2. **轉換邏輯集中管理**：所有轉換邏輯放在 `converters/` 目錄
3. **路由函數保持簡潔**：只處理 HTTP 相關邏輯
4. **重用轉換器**：多個路由使用相同的轉換邏輯時，重用轉換器
5. **類型提示完整**：所有函數都應該有完整的類型提示

### ❌ 不應該做的

1. **不要在路由中直接轉換**：避免重複代碼
2. **不要在 Schema 中加入轉換邏輯**：保持 Schema 純粹
3. **不要在轉換器中加入業務邏輯**：業務邏輯應在 Service 層
4. **不要跳過轉換器**：即使轉換很簡單，也應該使用轉換器保持一致性

---

## 與其他層的關係

### 與 Domain 層

- **依賴方向**：API 層依賴 Domain 層（單向）
- **轉換方向**：Domain Model → API Schema（透過轉換器）

### 與 Service 層

- **依賴方向**：API 層依賴 Service 層（透過 `deps.py` 注入）
- **呼叫方式**：路由函數直接呼叫 Service 方法

### 與 Infrastructure 層

- **無直接依賴**：API 層不直接依賴 Infrastructure 層
- **間接依賴**：透過 Service 層間接使用 Infrastructure

---

## 總結

API 層的架構設計遵循以下原則：

1. **職責分離**：Schema、轉換器、路由各司其職
2. **按資源組織**：Schema 和轉換器都按資源分檔
3. **獨立轉換器**：Domain → Schema 轉換邏輯獨立管理
4. **保持純粹**：Schema 只負責資料結構定義
5. **易於擴展**：新增資源時遵循相同的組織規範

這樣的設計確保了：
- ✅ 程式碼清晰易讀
- ✅ 易於測試與維護
- ✅ 符合 Clean Architecture 原則
- ✅ 易於擴展新功能

