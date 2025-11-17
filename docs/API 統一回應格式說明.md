# API 統一回應格式說明

## 概述

本專案採用統一的 API 回應格式，確保前端能夠統一處理所有 API 的回應，提升開發效率和用戶體驗。

---

## 為什麼需要統一回應格式？

### 問題

在沒有統一格式的情況下，API 回應可能千變萬化：

```
// API 1
{
  "user_id": "123",
  "items": []
}

// API 2
{
  "data": {...}
}

// API 3 錯誤
{
  "detail": "錯誤訊息"
}
```

前端需要針對每個 API 編寫不同的處理邏輯。

### 解決方案

採用統一的回應格式：

```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

前端可以統一處理：
- 通過 `success` 判斷請求是否成功
- 通過 `code` 處理業務狀態碼
- 通過 `message` 顯示提示訊息
- 通過 `data` 獲取實際數據

---

## 回應格式定義

### 成功回應格式

```typescript
{
  success: boolean;      // 請求是否成功（true）
  code: number;          // 業務狀態碼（通常與 HTTP 狀態碼一致）
  message: string;       // 回應訊息
  data: T | null;        // 實際的回應資料（泛型）
  timestamp: string;     // ISO 8601 格式的時間戳
}
```

**範例：**

```json
{
  "success": true,
  "code": 200,
  "message": "獲取購物車成功",
  "data": {
    "user_id": "user123",
    "items": [
      {
        "product_id": "prod456",
        "quantity": 2,
        "unit_price": 1000
      }
    ],
    "total": 2000
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 錯誤回應格式

```typescript
{
  success: boolean;      // 永遠為 false
  code: number;          // 錯誤狀態碼
  message: string;       // 錯誤訊息
  errors?: Array<{       // 詳細錯誤列表（可選）
    field?: string;      // 出錯的欄位名稱
    message: string;     // 錯誤訊息
    code?: string;       // 錯誤代碼
  }>;
  timestamp: string;     // ISO 8601 格式的時間戳
}
```

**範例：**

```json
{
  "success": false,
  "code": 422,
  "message": "輸入驗證失敗",
  "errors": [
    {
      "field": "email",
      "message": "value is not a valid email address",
      "code": "value_error.email"
    },
    {
      "field": "quantity",
      "message": "ensure this value is greater than 0",
      "code": "value_error.number.not_gt"
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 分頁回應格式

```typescript
{
  success: true,
  code: 200,
  message: string;
  data: {
    items: T[];          // 當前頁的項目列表
    total: number;       // 總項目數
    page: number;        // 當前頁碼（從 1 開始）
    page_size: number;   // 每頁項目數
    total_pages: number; // 總頁數
  };
  timestamp: string;
}
```

**範例：**

```json
{
  "success": true,
  "code": 200,
  "message": "查詢成功",
  "data": {
    "items": [
      {"id": 1, "name": "Item 1"},
      {"id": 2, "name": "Item 2"}
    ],
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 使用方式

### 在路由中使用

#### 1. 成功回應

```python
from app.api.schemas.response import ApiResponse
from app.api.schemas.cart import CartOut
from app.api.utils.response import success_response

@router.get("/cart", response_model=ApiResponse[CartOut])
def get_cart(user_id: str, service: CartService = ...):
    """獲取購物車"""
    cart = service.get_cart(user_id)
    cart_data = cart_out_from_domain(cart)
    
    return success_response(
        data=cart_data,
        message="獲取購物車成功"
    )
```

#### 2. 創建資源回應（201）

```python
from app.api.utils.response import created_response

@router.post("/cart/items", response_model=ApiResponse[CartOut])
def add_item(body: AddItemIn, service: CartService = ...):
    """加入購物車項目"""
    cart = service.add_item(...)
    cart_data = cart_out_from_domain(cart)
    
    return created_response(
        data=cart_data,
        message="商品已成功加入購物車"
    )
```

#### 3. 分頁回應

```python
from app.api.utils.response import paginated_response

@router.get("/users", response_model=ApiResponse[PaginatedData[UserOut]])
def list_users(page: int = 1, page_size: int = 10):
    """獲取用戶列表"""
    users = service.list_users(page=page, page_size=page_size)
    total = service.count_users()
    
    return paginated_response(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        message="查詢成功"
    )
```

#### 4. 手動錯誤處理

```python
from fastapi import HTTPException, status
from app.api.utils.response import not_found_response

@router.get("/cart", response_model=ApiResponse[CartOut])
def get_cart(user_id: str, service: CartService = ...):
    """獲取購物車"""
    cart = service.get_cart(user_id)
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_response(
                resource_type="購物車",
                resource_id=user_id
            ).model_dump()
        )
    
    cart_data = cart_out_from_domain(cart)
    return success_response(data=cart_data, message="獲取購物車成功")
```

---

## 全局異常處理

本專案已配置全局異常處理器，自動捕獲並轉換異常為統一格式。

### 支援的異常類型

#### 1. RequestValidationError（422）

**觸發時機：** Pydantic 驗證失敗

**回應範例：**

```json
{
  "success": false,
  "code": 422,
  "message": "輸入驗證失敗",
  "errors": [
    {
      "field": "email",
      "message": "value is not a valid email address",
      "code": "value_error.email"
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 2. ValueError（400）

**觸發時機：** 業務邏輯驗證失敗

**回應範例：**

```json
{
  "success": false,
  "code": 400,
  "message": "請求參數錯誤",
  "errors": [
    {
      "message": "quantity must be positive"
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 3. Exception（500）

**觸發時機：** 未捕獲的異常

**回應範例（開發環境）：**

```json
{
  "success": false,
  "code": 500,
  "message": "伺服器內部錯誤",
  "errors": [
    {
      "message": "division by zero"
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**回應範例（生產環境）：**

```json
{
  "success": false,
  "code": 500,
  "message": "伺服器內部錯誤",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 前端整合範例

### TypeScript 類型定義

```typescript
// types/api.ts
export interface ApiResponse<T = any> {
  success: boolean;
  code: number;
  message: string;
  data: T | null;
  timestamp: string;
}

export interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

export interface ErrorResponse {
  success: false;
  code: number;
  message: string;
  errors?: ErrorDetail[];
  timestamp: string;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

### Axios 攔截器

```typescript
// api/interceptors.ts
import axios from 'axios';
import type { ApiResponse, ErrorResponse } from '@/types/api';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// 回應攔截器
api.interceptors.response.use(
  (response) => {
    const data: ApiResponse = response.data;
    
    // 檢查業務層面是否成功
    if (!data.success) {
      return Promise.reject({
        code: data.code,
        message: data.message,
        errors: (data as ErrorResponse).errors,
      });
    }
    
    return data;
  },
  (error) => {
    // HTTP 錯誤
    const data: ErrorResponse = error.response?.data;
    
    return Promise.reject({
      code: data?.code || error.response?.status || 500,
      message: data?.message || '網絡錯誤',
      errors: data?.errors,
    });
  }
);

export default api;
```

### 使用範例

```typescript
// services/cart.ts
import api from '@/api/interceptors';
import type { ApiResponse } from '@/types/api';

interface CartOut {
  user_id: string;
  items: Array<{
    product_id: string;
    quantity: number;
    unit_price: number;
  }>;
  total: number;
}

export async function getCart(userId: string): Promise<CartOut> {
  const response = await api.get<ApiResponse<CartOut>>('/cart', {
    params: { user_id: userId }
  });
  
  return response.data!;  // data 已在攔截器中驗證
}

// 在組件中使用
async function fetchCart() {
  try {
    const cart = await getCart('user123');
    console.log('購物車數據:', cart);
  } catch (error: any) {
    console.error('錯誤:', error.message);
    
    // 顯示詳細錯誤
    if (error.errors) {
      error.errors.forEach((err: ErrorDetail) => {
        console.error(`欄位 ${err.field}: ${err.message}`);
      });
    }
  }
}
```

---

## 狀態碼約定

### 成功狀態碼

| 狀態碼 | 說明 | 使用場景 |
|-------|------|---------|
| 200 | OK | 查詢、更新、刪除成功 |
| 201 | Created | 資源創建成功 |
| 204 | No Content | 刪除成功（無返回內容） |

### 客戶端錯誤狀態碼

| 狀態碼 | 說明 | 使用場景 |
|-------|------|---------|
| 400 | Bad Request | 請求參數錯誤、業務邏輯驗證失敗 |
| 401 | Unauthorized | 未授權、Token 無效 |
| 403 | Forbidden | 無權限訪問 |
| 404 | Not Found | 資源不存在 |
| 409 | Conflict | 資源衝突（如 Email 已存在） |
| 422 | Unprocessable Entity | 輸入驗證失敗 |
| 429 | Too Many Requests | 請求過於頻繁 |

### 伺服器錯誤狀態碼

| 狀態碼 | 說明 | 使用場景 |
|-------|------|---------|
| 500 | Internal Server Error | 伺服器內部錯誤 |
| 502 | Bad Gateway | 網關錯誤 |
| 503 | Service Unavailable | 服務不可用 |

---

## 最佳實踐

### 1. 訊息應該清晰友好

```python
# ✅ 好的訊息
return success_response(
    data=cart_data,
    message="商品已成功加入購物車"
)

# ❌ 不好的訊息
return success_response(
    data=cart_data,
    message="success"
)
```

### 2. 錯誤訊息應該具體

```python
# ✅ 好的錯誤訊息
raise ValueError(f"商品 {product_id} 庫存不足")

# ❌ 不好的錯誤訊息
raise ValueError("error")
```

### 3. 使用正確的狀態碼

```python
# ✅ 創建資源使用 201
return created_response(data=user, message="用戶創建成功")

# ❌ 創建資源不應該使用 200
return success_response(data=user, message="用戶創建成功")
```

### 4. 提供詳細的驗證錯誤

```python
# ✅ 詳細的錯誤信息（自動由全局處理器處理）
# Pydantic 會自動提供 field 和 message

# ❌ 不要手動拋出沒有結構的錯誤
raise HTTPException(status_code=400, detail="invalid input")
```

### 5. 在 Service 層拋出有意義的異常

```python
# core/services/cart_service.py

class CartService:
    def add_item(self, user_id: str, product_id: str, quantity: int, ...):
        """加入購物車項目"""
        
        # ✅ 拋出有意義的業務異常
        if quantity <= 0:
            raise ValueError("商品數量必須大於 0")
        
        if not self.product_exists(product_id):
            raise ValueError(f"商品 {product_id} 不存在")
        
        # 業務邏輯...
```

---

## 測試範例

### 單元測試

```python
# tests/api/test_carts.py
import pytest
from fastapi.testclient import TestClient

def test_get_cart_success(client: TestClient):
    """測試獲取購物車成功"""
    response = client.get("/api/cart?user_id=user123")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["code"] == 200
    assert data["message"] == "獲取購物車成功"
    assert "data" in data
    assert "timestamp" in data

def test_get_cart_not_found(client: TestClient):
    """測試購物車不存在"""
    response = client.get("/api/cart?user_id=nonexistent")
    
    assert response.status_code == 404
    
    data = response.json()
    assert data["success"] is False
    assert data["code"] == 404
    assert "購物車" in data["message"]

def test_add_item_validation_error(client: TestClient):
    """測試輸入驗證失敗"""
    response = client.post(
        "/api/cart/items?user_id=user123",
        json={
            "product_id": "prod456",
            "quantity": 0,  # 無效數量
            "unit_price": -100  # 無效價格
        }
    )
    
    assert response.status_code == 422
    
    data = response.json()
    assert data["success"] is False
    assert data["code"] == 422
    assert "errors" in data
    assert len(data["errors"]) > 0
```

---

## 總結

統一的 API 回應格式帶來以下優勢：

1. ✅ **前端統一處理**：一套攔截器處理所有 API
2. ✅ **清晰的錯誤信息**：結構化的錯誤詳情
3. ✅ **類型安全**：TypeScript 完整類型支援
4. ✅ **易於調試**：時間戳和詳細錯誤碼
5. ✅ **自動化處理**：全局異常處理器自動轉換
6. ✅ **向後兼容**：新舊前端都能正常工作

---

## 相關文檔

- [API 層架構設計.md](./API%20層架構設計.md)
- [架構說明.md](./架構說明.md)
- [Clean Architecture 同心圓架構詳解.md](./Clean%20Architecture%20同心圓架構詳解.md)

