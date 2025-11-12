# 新增功能指南：User CRUD - 基礎架構

## 概述

本文檔說明如何根據現有架構新增 User 相關的 RESTful API。在實作 CRUD 操作之前，需要先建立基礎架構。

## 架構層級

根據 Clean Architecture 原則，需要建立以下層級：

```
1. Domain 層（core/domain/user.py）
   └── User 領域模型

2. Repository 接口層（core/repositories/user_repository.py）
   └── UserRepository 抽象接口

3. Repository 實現層（infra/db/repositories/user_repository_impl.py）
   └── UserRepositoryImpl 具體實現

4. Service 層（core/services/user_service.py）
   └── UserService 業務邏輯

5. API Schema 層（api/schemas/user.py）
   └── User 相關的 Request/Response Schema

6. Converter 層（api/utils/converters/user.py）
   └── Domain Model → API Schema 轉換器

7. API 路由層（api/users.py）
   └── RESTful API 端點

8. 依賴注入（api/deps.py）
   └── get_user_service 函數
```

---

## 步驟 1：建立 Domain 模型

**檔案：`core/domain/user.py`**

```python
"""
User 領域模型

定義 User 實體的業務邏輯和行為。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """用戶領域模型"""
    id: Optional[int] = None
    email: str = ""
    name: str = ""
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化後驗證"""
        if not self.email:
            raise ValueError("email is required")
        if not self.name:
            raise ValueError("name is required")
```

**說明：**
- 使用 `@dataclass` 定義領域模型
- 包含業務驗證邏輯
- 不依賴任何外部框架

---

## 步驟 2：建立 Repository 接口

**檔案：`core/repositories/user_repository.py`**

```python
"""
User Repository 接口

定義 User 資料存取的抽象接口。
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.core.domain.user import User


class UserRepository(ABC):
    """User Repository 抽象接口"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """創建用戶"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取用戶"""
        raise NotImplementedError
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """根據 Email 獲取用戶"""
        raise NotImplementedError
    
    @abstractmethod
    def get_all(self) -> List[User]:
        """獲取所有用戶"""
        raise NotImplementedError
    
    @abstractmethod
    def update(self, user: User) -> User:
        """更新用戶"""
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, user_id: int) -> None:
        """刪除用戶"""
        raise NotImplementedError
```

**說明：**
- 定義所有 CRUD 操作的抽象方法
- 使用 `ABC` 和 `@abstractmethod` 確保必須實現

---

## 步驟 3：建立資料庫 Model

**檔案：`infra/db/models/user.py`**

```python
"""
User 資料庫模型

定義 User 在資料庫中的結構。
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.infra.db.base import Base


class UserModel(Base):
    """User 資料庫模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**說明：**
- 繼承 `Base`（SQLAlchemy 的 declarative_base）
- 定義資料表結構
- 使用 `server_default` 自動設置創建時間

---

## 步驟 4：建立 Repository 實現

**檔案：`infra/db/repositories/user_repository_impl.py`**

```python
"""
User Repository 實現

使用 SQLAlchemy 實現 UserRepository 接口。
"""
from typing import Optional, List

from sqlalchemy.orm import Session

from app.core.domain.user import User
from app.core.repositories.user_repository import UserRepository
from app.infra.db.models.user import UserModel
from app.infra.db.repositories.base_repository import SqlAlchemyRepositoryBase


class UserRepositoryImpl(SqlAlchemyRepositoryBase, UserRepository):
    """
    User Repository 實作類
    
    使用多重繼承：
    1. SqlAlchemyRepositoryBase - 提供通用 CRUD 操作
    2. UserRepository - 實現業務接口契約
    """
    
    def __init__(self, session: Session):
        """
        初始化 Repository
        
        :param session: SQLAlchemy Session 實例（通過依賴注入）
        """
        SqlAlchemyRepositoryBase.__init__(self, session, UserModel)
    
    def create(self, user: User) -> User:
        """創建用戶"""
        user_model = UserModel(
            email=user.email,
            name=user.name,
        )
        saved_model = self.save(user_model)
        return self._model_to_domain(saved_model)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """根據 ID 獲取用戶"""
        model = self.get(user_id)
        if not model:
            return None
        return self._model_to_domain(model)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根據 Email 獲取用戶"""
        model = self.first(email=email)
        if not model:
            return None
        return self._model_to_domain(model)
    
    def get_all(self) -> List[User]:
        """獲取所有用戶"""
        models = self.all()
        return [self._model_to_domain(model) for model in models]
    
    def update(self, user: User) -> User:
        """更新用戶"""
        if not user.id:
            raise ValueError("user.id is required for update")
        
        model = self.get(user.id)
        if not model:
            raise ValueError(f"User with id {user.id} not found")
        
        model.email = user.email
        model.name = user.name
        
        saved_model = self.save(model)
        return self._model_to_domain(saved_model)
    
    def delete(self, user_id: int) -> None:
        """刪除用戶"""
        self.delete(user_id)
    
    def _model_to_domain(self, model: UserModel) -> User:
        """將資料庫模型轉換為領域模型"""
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            created_at=model.created_at,
        )
```

**說明：**
- 繼承 `SqlAlchemyRepositoryBase` 獲得通用 CRUD 方法
- 實現 `UserRepository` 接口的所有方法
- 提供 `_model_to_domain` 轉換方法

---

## 步驟 5：建立 Service 層

**檔案：`core/services/user_service.py`**

```python
"""
User Service

處理 User 相關的業務邏輯。
"""
from typing import Optional, List

from app.core.domain.user import User
from app.core.repositories.user_repository import UserRepository


class UserService:
    """User 業務邏輯服務"""
    
    def __init__(self, user_repo: UserRepository):
        """
        初始化 Service
        
        :param user_repo: UserRepository 實例（通過依賴注入）
        """
        self.user_repo = user_repo
    
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
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        獲取用戶
        
        :param user_id: 用戶 ID
        :return: User 或 None
        """
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根據 Email 獲取用戶
        
        :param email: 用戶 Email
        :return: User 或 None
        """
        return self.user_repo.get_by_email(email)
    
    def list_users(self) -> List[User]:
        """
        獲取所有用戶
        
        :return: User 列表
        """
        return self.user_repo.get_all()
    
    def update_user(self, user_id: int, email: Optional[str] = None, name: Optional[str] = None) -> User:
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
- 包含業務邏輯（如 Email 唯一性檢查）
- 使用 Repository 進行資料存取
- 處理業務異常

---

## 步驟 6：建立 API Schema

**檔案：`api/schemas/user.py`**

```python
"""
User 相關的 API Schema

定義 User 相關的請求與回應資料結構。
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    """用戶回應 Schema"""
    id: int
    email: EmailStr
    name: str
    created_at: datetime


class UserCreateIn(BaseModel):
    """創建用戶請求 Schema"""
    email: EmailStr = Field(..., description="用戶 Email")
    name: str = Field(..., min_length=1, max_length=100, description="用戶名稱")


class UserUpdateIn(BaseModel):
    """更新用戶請求 Schema"""
    email: Optional[EmailStr] = Field(None, description="用戶 Email")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用戶名稱")
```

**說明：**
- 使用 Pydantic 進行資料驗證
- 分別定義 Request 和 Response Schema
- 使用 `EmailStr` 驗證 Email 格式

---

## 步驟 7：建立 Converter

**檔案：`api/utils/converters/user.py`**

```python
"""
User Domain Model 到 API Schema 的轉換器

負責將 core/domain 的 User 模型轉換為 API 層的 Schema。
"""
from app.core.domain.user import User
from app.api.schemas.user import UserOut


def user_out_from_domain(user: User) -> UserOut:
    """
    將 Domain User 轉換為 API UserOut
    
    :param user: Domain 層的 User
    :return: API 層的 UserOut
    """
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )
```

**說明：**
- 負責 Domain Model → API Schema 的轉換
- 保持轉換邏輯獨立

---

## 步驟 8：建立依賴注入

**檔案：`api/deps.py`**（追加）

```python
# 在現有檔案中追加

def get_user_service(
    session=Depends(get_session),
) -> UserService:
    """
    獲取 UserService 實例
    
    使用自動化機制，無需手動組裝依賴。
    """
    from app.core.services.user_service import UserService
    return get_service(UserService, session)
```

**說明：**
- 使用現有的自動化依賴注入機制
- 遵循與 `get_cart_service` 相同的模式

---

## 步驟 9：註冊路由

**檔案：`api/http_app.py`**（更新）

```python
from app.api import carts, users  # 新增 users

def create_http_app() -> FastAPI:
    # ...
    app.include_router(carts.router, prefix="/api")
    app.include_router(users.router, prefix="/api")  # 新增
    return app
```

---

## 步驟 10：建立資料庫遷移

使用 Alembic 建立資料庫遷移：

```bash
# 生成遷移檔案
alembic revision --autogenerate -m "add users table"

# 執行遷移
alembic upgrade head
```

---

## 檢查清單

完成基礎架構後，確認：

- [ ] Domain 模型已建立（`core/domain/user.py`）
- [ ] Repository 接口已建立（`core/repositories/user_repository.py`）
- [ ] 資料庫 Model 已建立（`infra/db/models/user.py`）
- [ ] Repository 實現已建立（`infra/db/repositories/user_repository_impl.py`）
- [ ] Service 層已建立（`core/services/user_service.py`）
- [ ] API Schema 已建立（`api/schemas/user.py`）
- [ ] Converter 已建立（`api/utils/converters/user.py`）
- [ ] 依賴注入已添加（`api/deps.py`）
- [ ] 路由已註冊（`api/http_app.py`）
- [ ] 資料庫遷移已建立並執行

---

## 下一步

完成基礎架構後，請參考以下文件實作具體的 CRUD 操作：

1. [Create 操作指南](新增功能指南-User CRUD-02-Create.md)
2. [Retrieve 操作指南](新增功能指南-User CRUD-03-Retrieve.md)
3. [Update 操作指南](新增功能指南-User CRUD-04-Update.md)
4. [Delete 操作指南](新增功能指南-User CRUD-05-Delete.md)

