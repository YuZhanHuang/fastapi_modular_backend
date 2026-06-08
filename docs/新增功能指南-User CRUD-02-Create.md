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

**檔案：`api/routers/users.py`**

```python
"""
User API 路由

處理 User 相關的 HTTP 請求。
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import inject_service
from app.api.schemas.user import UserOut, UserCreateIn
from app.api.utils.converters.user import user_out_from_domain
from app.core.services.user_service import UserService
from app.infra.containers import get_container

router = APIRouter(tags=["user"])
container = get_container()

UserServiceDep = Annotated[
    UserService,
    Depends(inject_service(container.services.user_service)),
]


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="創建用戶",
    description="創建一個新的用戶帳號"
)
def create_user(
    body: UserCreateIn,
    service: UserServiceDep,
) -> UserOut:
    """
    創建用戶
    
    - **email**: 用戶 Email（必須唯一）
    - **name**: 用戶名稱
    
    返回創建的用戶資訊。
    """
    user = service.create_user(
        email=body.email,
        name=body.name,
    )
    return user_out_from_domain(user)
```

**說明：**
- Router 模組放在 `api/routers/`，匯出 `router = APIRouter(...)` 後啟動時自動註冊
- 使用 `@router.post` 定義 POST 端點
- `status_code=201` 表示創建成功
- 使用 `UserServiceDep` 注入 Service（與 `CartServiceDep` 相同模式）
- Service 層拋出 `DomainError` 子類（如 `DuplicateEmailError`），由全局 handler 自動轉為 HTTP 回應
- 使用 Converter 轉換 Domain Model → API Schema

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
   api/routers/users.py::create_user()
   
3. Pydantic 驗證
   UserCreateIn(email="user@example.com", name="John Doe")
   
4. 依賴注入
   UserServiceDep → UserService 實例
   
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

手動驗證 API 使用 curl；自動化測試請用 `./scripts/test.sh`（見 [測試流程說明](測試流程說明.md)）。

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
- [ ] API 路由已實作（`api/routers/users.py` 且匯出 `router`）
- [ ] 錯誤處理已實作
- [ ] 測試通過（`./scripts/test.sh`）

---

## 相關文件

- [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)
- [Retrieve 操作指南](新增功能指南-User CRUD-03-Retrieve.md)

