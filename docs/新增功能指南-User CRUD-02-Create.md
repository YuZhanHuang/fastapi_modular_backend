# 新增功能指南：User CRUD - Create 操作

## 概述

本文檔說明如何實作 User 的 Create（創建）操作。假設基礎架構已經完成（參考 [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)）。

---

## API 規格

**端點：** `POST /api/users`

**請求：**
```json
{
  "email": "user@example.com",
  "name": "John Doe"
}
```

**回應：** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**錯誤回應：**
- `400 Bad Request` - 輸入驗證失敗
- `409 Conflict` - Email 已存在

---

## 實作步驟

### 步驟 1：確認 Service 方法已實作

**檔案：`core/services/user_service.py`**

確認 `create_user` 方法已實作：

```python
def create_user(self, email: str, name: str) -> User:
    """
    創建用戶
    
    :param email: 用戶 Email
    :param name: 用戶名稱
    :return: 創建的 User
    :raises ValueError: 如果 Email 已存在
    """
    # 檢查 Email 是否已存在
    existing_user = self.user_repo.get_by_email(email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")
    
    user = User(email=email, name=name)
    return self.user_repo.create(user)
```

**說明：**
- 業務邏輯：檢查 Email 唯一性
- 創建 User 領域模型
- 透過 Repository 保存

---

### 步驟 2：確認 Schema 已定義

**檔案：`api/schemas/user.py`**

確認 `UserCreateIn` 和 `UserOut` 已定義：

```python
class UserCreateIn(BaseModel):
    """創建用戶請求 Schema"""
    email: EmailStr = Field(..., description="用戶 Email")
    name: str = Field(..., min_length=1, max_length=100, description="用戶名稱")


class UserOut(BaseModel):
    """用戶回應 Schema"""
    id: int
    email: EmailStr
    name: str
    created_at: datetime
```

**說明：**
- `UserCreateIn`：請求驗證
- `UserOut`：回應格式
- 使用 `EmailStr` 自動驗證 Email 格式

---

### 步驟 3：確認 Converter 已實作

**檔案：`api/utils/converters/user.py`**

確認轉換函數已實作：

```python
def user_out_from_domain(user: User) -> UserOut:
    """將 Domain User 轉換為 API UserOut"""
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )
```

---

### 步驟 4：實作 API 路由

**檔案：`api/users.py`**

```python
"""
User API 路由

處理 User 相關的 HTTP 請求。
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_user_service
from app.api.schemas.user import UserOut, UserCreateIn
from app.api.utils.converters.user import user_out_from_domain
from app.core.services.user_service import UserService

router = APIRouter(tags=["users"])


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="創建用戶",
    description="創建一個新的用戶帳號"
)
def create_user(
    body: UserCreateIn,
    service: UserService = Depends(get_user_service),
) -> UserOut:
    """
    創建用戶
    
    - **email**: 用戶 Email（必須唯一）
    - **name**: 用戶名稱
    
    返回創建的用戶資訊。
    """
    try:
        # 呼叫 Service 層創建用戶
        user = service.create_user(
            email=body.email,
            name=body.name,
        )
        
        # 轉換為 API Schema 並返回
        return user_out_from_domain(user)
        
    except ValueError as e:
        # 處理業務邏輯錯誤（如 Email 已存在）
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

**說明：**
- 使用 `@router.post` 定義 POST 端點
- `status_code=201` 表示創建成功
- 使用 `Depends(get_user_service)` 注入 Service
- 處理 `ValueError` 並轉換為適當的 HTTP 狀態碼
- 使用 Converter 轉換 Domain Model → API Schema

---

### 步驟 5：註冊路由

**檔案：`api/http_app.py`**

確認路由已註冊：

```python
from app.api import carts, users

def create_http_app() -> FastAPI:
    app = FastAPI(
        title="Cart Service",
        version="1.0.0",
    )

    app.include_router(carts.router, prefix="/api")
    app.include_router(users.router, prefix="/api")  # 新增

    return app
```

---

## 完整流程

```
1. HTTP 請求
   POST /api/users
   {
     "email": "user@example.com",
     "name": "John Doe"
   }
   
2. FastAPI 路由處理
   api/users.py::create_user()
   
3. Pydantic 驗證
   UserCreateIn(email="user@example.com", name="John Doe")
   
4. 依賴注入
   get_user_service() → UserService 實例
   
5. Service 層處理
   UserService.create_user()
   - 檢查 Email 唯一性
   - 創建 User 領域模型
   
6. Repository 層處理
   UserRepositoryImpl.create()
   - 轉換為 UserModel
   - 保存到資料庫
   - 返回 UserModel
   
7. 轉換為領域模型
   UserRepositoryImpl._model_to_domain()
   
8. 轉換為 API Schema
   user_out_from_domain() → UserOut
   
9. 返回 HTTP 回應
   201 Created
   {
     "id": 1,
     "email": "user@example.com",
     "name": "John Doe",
     "created_at": "2024-01-01T00:00:00Z"
   }
```

---

## 測試

### 使用 curl 測試

```bash
# 創建用戶
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe"
  }'

# 預期回應：201 Created
```

### 使用 Python 測試

```python
import requests

response = requests.post(
    "http://localhost:8000/api/users",
    json={
        "email": "user@example.com",
        "name": "John Doe"
    }
)

print(response.status_code)  # 201
print(response.json())
```

---

## 錯誤處理

### 1. Email 已存在

**請求：**
```json
{
  "email": "existing@example.com",
  "name": "John Doe"
}
```

**回應：** `409 Conflict`
```json
{
  "detail": "User with email existing@example.com already exists"
}
```

### 2. 輸入驗證失敗

**請求：**
```json
{
  "email": "invalid-email",
  "name": ""
}
```

**回應：** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 檢查清單

- [ ] Service 方法已實作
- [ ] Schema 已定義
- [ ] Converter 已實作
- [ ] API 路由已實作
- [ ] 路由已註冊
- [ ] 錯誤處理已實作
- [ ] 測試通過

---

## 相關文件

- [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)
- [Retrieve 操作指南](新增功能指南-User CRUD-03-Retrieve.md)

