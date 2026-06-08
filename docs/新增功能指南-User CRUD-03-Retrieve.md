# 新增功能指南：User CRUD - Retrieve 操作

## 概述

本文檔說明如何實作 User 的 Retrieve（查詢）操作，包括：
- 根據 ID 獲取單一用戶
- 獲取所有用戶列表

假設基礎架構已經完成（參考 [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)）。

---

## API 規格

### 1. 根據 ID 獲取用戶

**端點：** `GET /api/users/{user_id}`

**回應：** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**錯誤回應：**
- `404 Not Found` - 用戶不存在

---

### 2. 獲取所有用戶

**端點：** `GET /api/users`

**回應：** `200 OK`
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "email": "user2@example.com",
    "name": "Jane Smith",
    "created_at": "2024-01-02T00:00:00Z"
  }
]
```

---

## 實作步驟

### 步驟 1：確認 Service 方法已實作

**檔案：`core/services/user_service.py`**

確認以下方法已實作：

```python
def get_user(self, user_id: int) -> Optional[User]:
    """
    獲取用戶
    
    :param user_id: 用戶 ID
    :return: User 或 None
    """
    return self.user_repo.get_by_id(user_id)

def list_users(self) -> List[User]:
    """
    獲取所有用戶
    
    :return: User 列表
    """
    return self.user_repo.get_all()
```

---

### 步驟 2：實作 API 路由

**檔案：`api/routers/users.py`**

在現有檔案中追加以下路由：

```python
from typing import Annotated, List

from fastapi import APIRouter, Depends, Path

from app.api.deps import inject_service
from app.api.schemas.user import UserOut
from app.api.utils.converters.user import user_out_from_domain
from app.core.services.user_service import UserService
from app.infra.containers import get_container

router = APIRouter(tags=["user"])
container = get_container()

UserServiceDep = Annotated[
    UserService,
    Depends(inject_service(container.services.user_service)),
]


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    summary="獲取用戶",
    description="根據 ID 獲取單一用戶資訊"
)
def get_user(
    user_id: int = Path(..., description="用戶 ID", gt=0),
    service: UserServiceDep,
) -> UserOut:
    """
    根據 ID 獲取用戶
    
    - **user_id**: 用戶 ID（路徑參數）
    
    返回用戶資訊，如果用戶不存在則返回 404。
    """
    user = service.get_user(user_id)  # 不存在時 Service 拋出 UserNotFoundError
    return user_out_from_domain(user)


@router.get(
    "/users",
    response_model=List[UserOut],
    summary="獲取所有用戶",
    description="獲取所有用戶列表"
)
def list_users(
    service: UserServiceDep,
) -> List[UserOut]:
    """
    獲取所有用戶
    
    返回所有用戶的列表。
    """
    users = service.list_users()
    return [user_out_from_domain(user) for user in users]
```

**說明：**
- `GET /users/{user_id}`：使用路徑參數獲取單一用戶
- `GET /users`：獲取所有用戶列表
- 使用 `Path(..., gt=0)` 驗證 user_id 必須大於 0
- 處理 404 錯誤（用戶不存在）
- 使用列表推導式批量轉換

---

## 完整流程

### 獲取單一用戶流程

```
1. HTTP 請求
   GET /api/users/1
   
2. FastAPI 路由處理
   api/routers/users.py::get_user(user_id=1)
   
3. 路徑參數驗證
   user_id = 1 (必須 > 0)
   
4. 依賴注入
   UserServiceDep → UserService 實例
   
5. Service 層處理
   UserService.get_user(user_id=1)
   
6. Repository 層處理
   UserRepositoryImpl.get_by_id(1)
   - 查詢資料庫
   - 返回 UserModel 或 None
   
7. 轉換為領域模型
   UserRepositoryImpl._model_to_domain()
   
8. 檢查是否存在
   if not user: raise 404
   
9. 轉換為 API Schema
   user_out_from_domain() → UserOut
   
10. 返回 HTTP 回應
    200 OK
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2024-01-01T00:00:00Z"
    }
```

### 獲取所有用戶流程

```
1. HTTP 請求
   GET /api/users
   
2. FastAPI 路由處理
   api/routers/users.py::list_users()
   
3. 依賴注入
   UserServiceDep → UserService 實例
   
4. Service 層處理
   UserService.list_users()
   
5. Repository 層處理
   UserRepositoryImpl.get_all()
   - 查詢所有記錄
   - 返回 UserModel 列表
   
6. 批量轉換為領域模型
   [UserRepositoryImpl._model_to_domain(model) for model in models]
   
7. 批量轉換為 API Schema
   [user_out_from_domain(user) for user in users]
   
8. 返回 HTTP 回應
   200 OK
   [
     {
       "id": 1,
       "email": "user1@example.com",
       "name": "John Doe",
       "created_at": "2024-01-01T00:00:00Z"
     },
     ...
   ]
```

---

## 測試

### 使用 curl 測試

```bash
# 獲取單一用戶
curl -X GET "http://localhost:8000/api/users/1"

# 預期回應：200 OK
# {
#   "id": 1,
#   "email": "user@example.com",
#   "name": "John Doe",
#   "created_at": "2024-01-01T00:00:00Z"
# }

# 獲取所有用戶
curl -X GET "http://localhost:8000/api/users"

# 預期回應：200 OK
# [
#   {
#     "id": 1,
#     "email": "user1@example.com",
#     "name": "John Doe",
#     "created_at": "2024-01-01T00:00:00Z"
#   },
#   ...
# ]
```

### 使用 Python 測試

```python
import requests

# 獲取單一用戶
response = requests.get("http://localhost:8000/api/users/1")
print(response.status_code)  # 200
print(response.json())

# 獲取所有用戶
response = requests.get("http://localhost:8000/api/users")
print(response.status_code)  # 200
print(response.json())  # 列表
```

---

## 錯誤處理

### 1. 用戶不存在

**請求：** `GET /api/users/999`

**回應：** `404 Not Found`
```json
{
  "detail": "User with id 999 not found"
}
```

### 2. 無效的 user_id

**請求：** `GET /api/users/0`

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

### 3. 空列表

**請求：** `GET /api/users`（當資料庫中沒有用戶時）

**回應：** `200 OK`
```json
[]
```

---

## 進階功能（可選）

### 分頁支援

列表 endpoint 建議使用統一 `ApiResponse[PaginatedData[UserOut]]` 格式。
API 層接收 `page` / `page_size`，透過 `PageParams.from_page()` 轉為 Core 的 `offset` / `limit`：

```python
from fastapi import Query

from app.api.schemas.response import ApiResponse, PaginatedData
from app.api.utils.response import paginated_response
from app.core.types.pagination import PageParams

@router.get(
    "/users",
    response_model=ApiResponse[PaginatedData[UserOut]],
)
def list_users(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(10, ge=1, le=100, description="每頁筆數"),
    service: UserServiceDep,
):
    """獲取用戶列表（分頁）"""
    result = service.list_users(PageParams.from_page(page, page_size))
    return paginated_response(
        items=[user_out_from_domain(u) for u in result.items],
        total=result.total,
        page=page,
        page_size=page_size,
        message="查詢成功",
    )
```

**分層說明：**
- **API**：`page` / `page_size` → `paginated_response()` 組裝 `PaginatedData`
- **Core**：`PageParams`（`offset` / `limit`）→ `PageResult`（`items` + `total`）
- **Infra**：`SqlAlchemyRepositoryBase.find_paginated()` 執行 SQL `OFFSET` / `LIMIT` + `COUNT`

### 搜尋功能

如果需要搜尋功能：

```python
@router.get(
    "/users/search",
    response_model=List[UserOut],
)
def search_users(
    q: str = Query(..., min_length=1, description="搜尋關鍵字"),
    service: UserServiceDep,
) -> List[UserOut]:
    """搜尋用戶"""
    users = service.search_users(query=q)
    return [user_out_from_domain(user) for user in users]
```

---

## 檢查清單

- [ ] Service 方法已實作（`get_user`, `list_users`）
- [ ] API 路由已實作
- [ ] 路徑參數驗證已添加
- [ ] 404 錯誤處理已實作
- [ ] Converter 已實作
- [ ] 測試通過

---

## 相關文件

- [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)
- [Create 操作指南](新增功能指南-User CRUD-02-Create.md)
- [Update 操作指南](新增功能指南-User CRUD-04-Update.md)

