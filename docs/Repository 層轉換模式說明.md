# Repository 層轉換模式說明

## 問題

在 Repository 實現層，是否需要將 SQLAlchemy Model 轉換為 Domain Model？

**範例：**
```python
def get_by_id(self, user_id: int) -> Optional[User]:
    model = self.get(user_id)  # SQLAlchemy Model
    if not model:
        return None
    return self._model_to_domain(model)  # 轉換為 Domain Model
```

---

## 答案：這是標準做法 ✅

根據 **Clean Architecture** 原則，**將 SQLAlchemy Model 轉換為 Domain Model 是標準且推薦的做法**。

---

## 為什麼需要轉換？

### 1. 符合依賴倒置原則（Dependency Inversion Principle）

**原則：**
- 高層模組不應該依賴低層模組
- 兩者都應該依賴抽象

**問題：**
- Domain Model 是**高層**（業務邏輯層）
- SQLAlchemy Model 是**低層**（基礎設施層）

**如果 Domain 層直接使用 SQLAlchemy Model：**
```
Domain Model → SQLAlchemy Model ❌
（高層依賴低層，違反原則）
```

**正確做法：**
```
Domain Model ← Repository 轉換 ← SQLAlchemy Model ✅
（高層不依賴低層，Repository 負責轉換）
```

### 2. 保持 Domain 層純粹

**Domain 層的職責：**
- ✅ 定義業務邏輯和規則
- ✅ 使用純 Python 物件
- ❌ **不應該依賴任何外部框架**

**如果 Domain Model 直接使用 SQLAlchemy Model：**
```python
# ❌ 錯誤：Domain 層依賴 SQLAlchemy
from sqlalchemy.orm import relationship
from app.infra.db.models.user import UserModel

class User:
    def __init__(self, model: UserModel):  # 依賴 SQLAlchemy
        self.id = model.id
        # ...
```

**正確做法：**
```python
# ✅ 正確：Domain 層是純 Python
from dataclasses import dataclass

@dataclass
class User:
    id: Optional[int] = None
    email: str = ""
    name: str = ""
    # 不依賴任何外部框架
```

### 3. 易於測試

**如果 Domain 層依賴 SQLAlchemy：**
- ❌ 測試時需要建立 SQLAlchemy Session
- ❌ 需要資料庫連接
- ❌ 測試速度慢
- ❌ 測試複雜度高

**使用 Domain Model：**
- ✅ 測試時只需建立純 Python 物件
- ✅ 不需要資料庫
- ✅ 測試速度快
- ✅ 測試簡單

**範例：**
```python
# ✅ 簡單的單元測試
def test_user_validation():
    user = User(email="test@example.com", name="Test")
    assert user.email == "test@example.com"
    # 不需要資料庫，不需要 SQLAlchemy
```

### 4. 易於切換資料庫

**如果 Domain 層依賴 SQLAlchemy：**
- ❌ 切換資料庫時需要修改 Domain 層
- ❌ 無法使用其他 ORM（如 Django ORM、Tortoise ORM）

**使用 Domain Model：**
- ✅ 切換資料庫時只需修改 Repository 實現
- ✅ Domain 層完全不受影響
- ✅ 可以輕鬆切換到其他 ORM 或資料庫

### 5. 避免 SQLAlchemy 特性洩漏

**SQLAlchemy Model 的特性：**
- Session 管理
- Lazy loading
- Relationship 載入
- 資料庫特定的行為

**如果這些特性洩漏到 Domain 層：**
- ❌ Service 層需要處理 SQLAlchemy Session
- ❌ 可能出現 Lazy loading 錯誤
- ❌ 業務邏輯與資料庫細節耦合

**使用 Domain Model：**
- ✅ Service 層只處理純 Python 物件
- ✅ 沒有 Lazy loading 問題
- ✅ 業務邏輯與資料庫完全解耦

---

## 轉換的實作方式

### 方式一：手動轉換（當前使用）

**優點：**
- ✅ 明確、清晰
- ✅ 完全控制轉換邏輯
- ✅ 易於除錯

**缺點：**
- ⚠️ 需要手動編寫轉換代碼
- ⚠️ 欄位多時較繁瑣

**範例：**
```python
def _model_to_domain(self, model: UserModel) -> User:
    """將資料庫模型轉換為領域模型"""
    return User(
        id=model.id,
        email=model.email,
        name=model.name,
        created_at=model.created_at,
    )
```

### 方式二：使用轉換工具（可選）

可以使用 `dataclasses` 或 `pydantic` 的轉換功能：

```python
def _model_to_domain(self, model: UserModel) -> User:
    """使用字典解包轉換"""
    return User(**{
        'id': model.id,
        'email': model.email,
        'name': model.name,
        'created_at': model.created_at,
    })
```

### 方式三：使用 Mapper 類別（複雜場景）

對於複雜的轉換邏輯，可以使用專門的 Mapper：

```python
class UserMapper:
    @staticmethod
    def to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            created_at=model.created_at,
        )
    
    @staticmethod
    def to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            name=user.name,
        )
```

---

## 現有專案中的實作

### Cart Repository 實作

**檔案：`infra/db/repositories/cart_repository_impl.py`**

```python
def get_by_user_id(self, user_id: str) -> Optional[Cart]:
    rows: List[CartItemModel] = self.find(user_id=user_id).all()
    
    if not rows:
        return None

    # ✅ 將資料庫模型轉換為領域模型
    return Cart(
        user_id=user_id,
        items=[
            CartItem(
                product_id=row.product_id,
                quantity=row.quantity,
                unit_price=row.unit_price,
            )
            for row in rows
        ],
    )
```

**說明：**
- ✅ 從 SQLAlchemy Model 轉換為 Domain Model
- ✅ Domain 層不依賴 SQLAlchemy
- ✅ 符合 Clean Architecture 原則

---

## 替代方案分析

### 方案 A：直接返回 SQLAlchemy Model（不推薦）❌

```python
def get_by_id(self, user_id: int) -> Optional[UserModel]:  # 返回 SQLAlchemy Model
    return self.get(user_id)
```

**問題：**
- ❌ Domain 層依賴 SQLAlchemy
- ❌ 違反依賴倒置原則
- ❌ 難以測試
- ❌ 無法切換資料庫

### 方案 B：使用 SQLAlchemy Hybrid Attributes（不推薦）❌

```python
class UserModel(Base):
    # ...
    
    @hybrid_property
    def to_domain(self):
        return User(id=self.id, email=self.email, ...)
```

**問題：**
- ❌ Domain 層仍然需要知道 SQLAlchemy
- ❌ 轉換邏輯混在 Model 中
- ❌ 違反單一職責原則

### 方案 C：轉換為 Domain Model（推薦）✅

```python
def get_by_id(self, user_id: int) -> Optional[User]:
    model = self.get(user_id)
    if not model:
        return None
    return self._model_to_domain(model)  # 轉換
```

**優點：**
- ✅ 符合 Clean Architecture
- ✅ Domain 層純粹
- ✅ 易於測試
- ✅ 易於切換資料庫

---

## 轉換的開銷

### 性能考量

**轉換開銷：**
- 創建新物件：O(n)（n 為欄位數）
- 記憶體：額外一份物件
- CPU：通常可忽略不計

**實際影響：**
- 對於大多數應用，轉換開銷**可忽略不計**
- 資料庫 I/O 才是瓶頸
- 轉換帶來的架構優勢遠大於性能開銷

**優化建議：**
- 如果性能確實是問題，可以考慮：
  - 快取轉換結果
  - 批量轉換優化
  - 使用更高效的轉換方式

---

## 最佳實踐

### 1. 統一轉換方法命名

```python
def _model_to_domain(self, model: UserModel) -> User:
    """將資料庫模型轉換為領域模型"""
    pass

def _domain_to_model(self, user: User) -> UserModel:
    """將領域模型轉換為資料庫模型"""
    pass
```

### 2. 在 Repository 層統一處理轉換

```python
class UserRepositoryImpl:
    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self.get(user_id)
        return self._model_to_domain(model) if model else None
    
    def create(self, user: User) -> User:
        model = self._domain_to_model(user)
        saved_model = self.save(model)
        return self._model_to_domain(saved_model)
```

### 3. 處理複雜轉換邏輯

```python
def _model_to_domain(self, model: UserModel) -> User:
    """處理複雜轉換邏輯"""
    return User(
        id=model.id,
        email=model.email,
        name=model.name,
        created_at=model.created_at,
        # 處理關聯資料
        orders=[self._order_model_to_domain(o) for o in model.orders] if hasattr(model, 'orders') else [],
    )
```

---

## 總結

### ✅ 標準做法

**將 SQLAlchemy Model 轉換為 Domain Model 是標準且推薦的做法。**

### 原因

1. ✅ **符合 Clean Architecture 原則**
2. ✅ **保持 Domain 層純粹**
3. ✅ **易於測試**
4. ✅ **易於切換資料庫**
5. ✅ **避免框架特性洩漏**

### 實作建議

1. ✅ 在 Repository 實現層統一處理轉換
2. ✅ 使用明確的轉換方法（如 `_model_to_domain`）
3. ✅ 保持轉換邏輯簡單清晰
4. ✅ 對於複雜場景，考慮使用 Mapper 類別

### 性能考量

- 轉換開銷通常可忽略不計
- 架構優勢遠大於性能開銷
- 如果確實有性能問題，再考慮優化

---

## 參考資料

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

