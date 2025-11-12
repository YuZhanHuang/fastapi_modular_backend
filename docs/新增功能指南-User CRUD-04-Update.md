# 新增功能指南：User CRUD - Update 操作

## 概述

本文檔說明如何實作 User 的 Update（更新）操作。假設基礎架構已經完成（參考 [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)）。

---

## API 規格

**端點：** `PUT /api/users/{user_id}`

**請求：**
```json
{
  "email": "newemail@example.com",
  "name": "Jane Doe"
}
```

**回應：** `200 OK`
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "name": "Jane Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**錯誤回應：**
- `400 Bad Request` - 輸入驗證失敗
- `404 Not Found` - 用戶不存在
- `409 Conflict` - Email 已存在

---

## 實作步驟

### 步驟 1：確認 Service 方法已實作

**檔案：`core/services/user_service.py`**

確認 `update_user` 方法已實作：

```python
def update_user(
    self,
    user_id: int,
    email: Optional[str] = None,
    name: Optional[str] = None
) -> User:
    """
    更新用戶
    
    :param user_id: 用戶 ID
    :param email: 新的 Email（可選）
    :param name: 新的名稱（可選）
    :return: 更新後的 User
    :raises ValueError: 如果用戶不存在或 Email 已存在
    """
    user = self.user_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    
    # 如果更新 Email，檢查是否已存在
    if email and email != user.email:
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        user.email = email
    
    if name:
        user.name = name
    
    return self.user_repo.update(user)
```

**說明：**
- 業務邏輯：檢查用戶是否存在
- 業務邏輯：檢查 Email 唯一性（如果更新 Email）
- 只更新提供的欄位（部分更新）

---

### 步驟 2：確認 Schema 已定義

**檔案：`api/schemas/user.py`**

確認 `UserUpdateIn` 已定義：

```python
class UserUpdateIn(BaseModel):
    """更新用戶請求 Schema"""
    email: Optional[EmailStr] = Field(None, description="用戶 Email")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用戶名稱")
```

**說明：**
- 所有欄位都是可選的（`Optional`）
- 允許部分更新
- 使用 `EmailStr` 驗證 Email 格式

---

### 步驟 3：實作 API 路由

**檔案：`api/users.py`**

在現有檔案中追加以下路由：

```python
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.api.deps import get_user_service
from app.api.schemas.user import UserOut, UserUpdateIn
from app.api.utils.converters.user import user_out_from_domain
from app.core.services.user_service import UserService

router = APIRouter(tags=["users"])


@router.put(
    "/users/{user_id}",
    response_model=UserOut,
    summary="更新用戶",
    description="更新用戶資訊（支援部分更新）"
)
def update_user(
    user_id: int = Path(..., description="用戶 ID", gt=0),
    body: UserUpdateIn = ...,
    service: UserService = Depends(get_user_service),
) -> UserOut:
    """
    更新用戶
    
    - **user_id**: 用戶 ID（路徑參數）
    - **email**: 新的 Email（可選）
    - **name**: 新的名稱（可選）
    
    支援部分更新，只更新提供的欄位。
    如果用戶不存在則返回 404。
    """
    try:
        # 呼叫 Service 層更新用戶
        user = service.update_user(
            user_id=user_id,
            email=body.email,
            name=body.name,
        )
        
        # 轉換為 API Schema 並返回
        return user_out_from_domain(user)
        
    except ValueError as e:
        # 處理業務邏輯錯誤
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "already exists" in str(e).lower():
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
- 使用 `@router.put` 定義 PUT 端點
- 使用路徑參數 `{user_id}` 指定要更新的用戶
- 使用 `UserUpdateIn` 進行請求驗證（所有欄位可選）
- 處理多種錯誤情況（404, 409, 400）

---

## 完整流程

```
1. HTTP 請求
   PUT /api/users/1
   {
     "email": "newemail@example.com",
     "name": "Jane Doe"
   }
   
2. FastAPI 路由處理
   api/users.py::update_user(user_id=1, body=UserUpdateIn(...))
   
3. 路徑參數驗證
   user_id = 1 (必須 > 0)
   
4. Pydantic 驗證
   UserUpdateIn(email="newemail@example.com", name="Jane Doe")
   
5. 依賴注入
   get_user_service() → UserService 實例
   
6. Service 層處理
   UserService.update_user(user_id=1, email="...", name="...")
   - 檢查用戶是否存在
   - 檢查 Email 唯一性（如果更新 Email）
   - 更新領域模型
   
7. Repository 層處理
   UserRepositoryImpl.update(user)
   - 查詢現有用戶
   - 更新欄位
   - 保存到資料庫
   
8. 轉換為領域模型
   UserRepositoryImpl._model_to_domain()
   
9. 轉換為 API Schema
   user_out_from_domain() → UserOut
   
10. 返回 HTTP 回應
    200 OK
    {
      "id": 1,
      "email": "newemail@example.com",
      "name": "Jane Doe",
      "created_at": "2024-01-01T00:00:00Z"
    }
```

---

## 測試

### 使用 curl 測試

```bash
# 更新用戶（更新所有欄位）
curl -X PUT "http://localhost:8000/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "name": "Jane Doe"
  }'

# 預期回應：200 OK

# 部分更新（只更新名稱）
curl -X PUT "http://localhost:8000/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Name"
  }'

# 部分更新（只更新 Email）
curl -X PUT "http://localhost:8000/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "another@example.com"
  }'
```

### 使用 Python 測試

```python
import requests

# 更新用戶
response = requests.put(
    "http://localhost:8000/api/users/1",
    json={
        "email": "newemail@example.com",
        "name": "Jane Doe"
    }
)

print(response.status_code)  # 200
print(response.json())

# 部分更新
response = requests.put(
    "http://localhost:8000/api/users/1",
    json={
        "name": "New Name"
    }
)

print(response.status_code)  # 200
print(response.json())
```

---

## 錯誤處理

### 1. 用戶不存在

**請求：** `PUT /api/users/999`
```json
{
  "name": "New Name"
}
```

**回應：** `404 Not Found`
```json
{
  "detail": "User with id 999 not found"
}
```

### 2. Email 已存在

**請求：** `PUT /api/users/1`
```json
{
  "email": "existing@example.com"
}
```

**回應：** `409 Conflict`
```json
{
  "detail": "User with email existing@example.com already exists"
}
```

### 3. 輸入驗證失敗

**請求：** `PUT /api/users/1`
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

### 4. 無效的 user_id

**請求：** `PUT /api/users/0`

**回應：** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["path", "user_id"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## 部分更新說明

### 支援的更新方式

1. **更新所有欄位**
```json
{
  "email": "newemail@example.com",
  "name": "New Name"
}
```

2. **只更新 Email**
```json
{
  "email": "newemail@example.com"
}
```

3. **只更新名稱**
```json
{
  "name": "New Name"
}
```

4. **空請求體（不更新）**
```json
{}
```

### 實作邏輯

在 Service 層中，只更新提供的欄位：

```python
# 如果提供了 email，才更新
if email and email != user.email:
    # 檢查唯一性並更新
    user.email = email

# 如果提供了 name，才更新
if name:
    user.name = name
```

---

## 檢查清單

- [ ] Service 方法已實作（`update_user`）
- [ ] Schema 已定義（`UserUpdateIn`）
- [ ] API 路由已實作
- [ ] 路徑參數驗證已添加
- [ ] 錯誤處理已實作（404, 409, 400）
- [ ] 部分更新功能正常
- [ ] Converter 已實作
- [ ] 測試通過

---

## 相關文件

- [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)
- [Create 操作指南](新增功能指南-User CRUD-02-Create.md)
- [Retrieve 操作指南](新增功能指南-User CRUD-03-Retrieve.md)
- [Delete 操作指南](新增功能指南-User CRUD-05-Delete.md)

