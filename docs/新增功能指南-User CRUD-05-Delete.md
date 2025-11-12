# 新增功能指南：User CRUD - Delete 操作

## 概述

本文檔說明如何實作 User 的 Delete（刪除）操作。假設基礎架構已經完成（參考 [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)）。

---

## API 規格

**端點：** `DELETE /api/users/{user_id}`

**回應：** `204 No Content`（成功時無回應內容）

**錯誤回應：**
- `404 Not Found` - 用戶不存在

---

## 實作步驟

### 步驟 1：確認 Service 方法已實作

**檔案：`core/services/user_service.py`**

確認 `delete_user` 方法已實作：

```python
def delete_user(self, user_id: int) -> None:
    """
    刪除用戶
    
    :param user_id: 用戶 ID
    :raises ValueError: 如果用戶不存在
    """
    user = self.user_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    
    self.user_repo.delete(user_id)
```

**說明：**
- 業務邏輯：檢查用戶是否存在
- 如果不存在則拋出異常
- 刪除操作不返回內容

---

### 步驟 2：實作 API 路由

**檔案：`api/users.py`**

在現有檔案中追加以下路由：

```python
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.api.deps import get_user_service
from app.core.services.user_service import UserService

router = APIRouter(tags=["users"])


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除用戶",
    description="刪除指定的用戶"
)
def delete_user(
    user_id: int = Path(..., description="用戶 ID", gt=0),
    service: UserService = Depends(get_user_service),
) -> None:
    """
    刪除用戶
    
    - **user_id**: 用戶 ID（路徑參數）
    
    成功刪除後返回 204 No Content。
    如果用戶不存在則返回 404。
    """
    try:
        service.delete_user(user_id)
        # 返回 None，FastAPI 會自動處理為 204 No Content
        return None
        
    except ValueError as e:
        # 處理業務邏輯錯誤（用戶不存在）
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

**說明：**
- 使用 `@router.delete` 定義 DELETE 端點
- `status_code=204` 表示成功刪除，無回應內容
- 使用路徑參數 `{user_id}` 指定要刪除的用戶
- 處理 404 錯誤（用戶不存在）
- 返回 `None`，FastAPI 會自動處理為 204 No Content

---

## 完整流程

```
1. HTTP 請求
   DELETE /api/users/1
   
2. FastAPI 路由處理
   api/users.py::delete_user(user_id=1)
   
3. 路徑參數驗證
   user_id = 1 (必須 > 0)
   
4. 依賴注入
   get_user_service() → UserService 實例
   
5. Service 層處理
   UserService.delete_user(user_id=1)
   - 檢查用戶是否存在
   - 如果不存在則拋出 ValueError
   
6. Repository 層處理
   UserRepositoryImpl.delete(1)
   - 從資料庫刪除記錄
   
7. 返回 HTTP 回應
   204 No Content（無回應內容）
```

---

## 測試

### 使用 curl 測試

```bash
# 刪除用戶
curl -X DELETE "http://localhost:8000/api/users/1"

# 預期回應：204 No Content（無內容）

# 驗證用戶已刪除
curl -X GET "http://localhost:8000/api/users/1"

# 預期回應：404 Not Found
```

### 使用 Python 測試

```python
import requests

# 刪除用戶
response = requests.delete("http://localhost:8000/api/users/1")
print(response.status_code)  # 204
print(response.text)  # 空字串

# 驗證用戶已刪除
response = requests.get("http://localhost:8000/api/users/1")
print(response.status_code)  # 404
```

---

## 錯誤處理

### 1. 用戶不存在

**請求：** `DELETE /api/users/999`

**回應：** `404 Not Found`
```json
{
  "detail": "User with id 999 not found"
}
```

### 2. 無效的 user_id

**請求：** `DELETE /api/users/0`

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

## 軟刪除（可選）

如果需要實作軟刪除（標記為已刪除而非真正刪除），可以這樣實作：

### 1. 更新 Domain 模型

**檔案：`core/domain/user.py`**

```python
@dataclass
class User:
    id: Optional[int] = None
    email: str = ""
    name: str = ""
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None  # 新增
    
    def is_deleted(self) -> bool:
        """檢查用戶是否已刪除"""
        return self.deleted_at is not None
```

### 2. 更新資料庫 Model

**檔案：`infra/db/models/user.py`**

```python
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 新增
```

### 3. 更新 Repository

**檔案：`infra/db/repositories/user_repository_impl.py`**

```python
def delete(self, user_id: int) -> None:
    """軟刪除用戶（標記為已刪除）"""
    model = self.get(user_id)
    if not model:
        raise ValueError(f"User with id {user_id} not found")
    
    model.deleted_at = datetime.now(timezone.utc)
    self.save(model)

def get_by_id(self, user_id: int) -> Optional[User]:
    """根據 ID 獲取用戶（排除已刪除的）"""
    model = self.first(id=user_id, deleted_at=None)  # 只查詢未刪除的
    if not model:
        return None
    return self._model_to_domain(model)
```

### 4. 更新 Service

**檔案：`core/services/user_service.py`**

```python
def delete_user(self, user_id: int) -> None:
    """軟刪除用戶"""
    user = self.user_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    
    if user.is_deleted():
        raise ValueError(f"User with id {user_id} is already deleted")
    
    self.user_repo.delete(user_id)
```

---

## 級聯刪除（可選）

如果需要刪除用戶時同時刪除相關資料（如購物車），可以這樣實作：

### 在 Service 層處理

**檔案：`core/services/user_service.py`**

```python
def delete_user(self, user_id: int) -> None:
    """刪除用戶及其相關資料"""
    user = self.user_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    
    # 刪除用戶的購物車（如果有的話）
    # cart_repo.delete_by_user_id(user_id)
    
    # 刪除用戶
    self.user_repo.delete(user_id)
```

---

## 檢查清單

- [ ] Service 方法已實作（`delete_user`）
- [ ] API 路由已實作
- [ ] 路徑參數驗證已添加
- [ ] 404 錯誤處理已實作
- [ ] 返回 204 No Content
- [ ] 測試通過
- [ ] （可選）軟刪除已實作
- [ ] （可選）級聯刪除已實作

---

## 相關文件

- [基礎架構指南](新增功能指南-User CRUD-01-基礎架構.md)
- [Create 操作指南](新增功能指南-User CRUD-02-Create.md)
- [Retrieve 操作指南](新增功能指南-User CRUD-03-Retrieve.md)
- [Update 操作指南](新增功能指南-User CRUD-04-Update.md)

---

## 總結

完成所有 CRUD 操作後，你的 User API 應該包含：

1. ✅ **Create** - `POST /api/users`
2. ✅ **Retrieve** - `GET /api/users/{user_id}` 和 `GET /api/users`
3. ✅ **Update** - `PUT /api/users/{user_id}`
4. ✅ **Delete** - `DELETE /api/users/{user_id}`

所有操作都遵循 Clean Architecture 原則，職責分離清晰，易於測試和維護。

