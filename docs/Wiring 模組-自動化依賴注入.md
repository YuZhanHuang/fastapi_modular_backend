# Wiring 模組 - 自動化依賴注入

## 概述

本模組實現了**自動發現 + 註冊表模式 + 泛型工廠**的依賴注入機制，解決重複代碼問題。

## 核心功能

### 1. 自動發現機制 (`auto_discovery.py`)

基於命名約定自動掃描和發現所有組件：

- **Repository 接口**：掃描 `core/repositories/` 目錄
- **Repository 實作**：掃描 `infra/db/repositories/` 目錄
- **Service 類別**：掃描 `core/services/` 目錄

**命名約定：**
- `{Entity}Repository` → `{Entity}RepositoryImpl`
- `{Entity}Service` → 自動解析依賴

### 2. 註冊表 (`registry.py`)

統一管理所有依賴映射關係：

- 自動建立 `Repository` → `RepositoryImpl` 映射
- 提供查詢接口
- 支持手動註冊（特殊情況）

### 3. 依賴解析器 (`dependency_resolver.py`)

自動解析 Service 的依賴：

- 分析 `__init__` 方法簽名
- 識別需要的 Repository/Port 類型
- 自動注入對應的實例

### 4. 泛型工廠 (`factories.py`)

統一的創建函數：

- `get_repository()` - 創建 Repository 實例
- `get_service()` - 創建 Service 實例，自動解析依賴

## 使用方式

### 基本使用

```python
from app.infra.wiring import get_service, get_repository
from app.core.services.cart_service import CartService
from app.core.repositories.cart_repository import CartRepository
from sqlalchemy.orm import Session

# 創建 Repository
repo = get_repository(CartRepository, session)

# 創建 Service（自動解析依賴）
service = get_service(CartService, session)
```

### 在 FastAPI 中使用

```python
# api/deps.py
from fastapi import Depends
from app.infra.db.session import get_session
from app.infra.wiring import get_service
from app.core.services.cart_service import CartService

def get_cart_service(
    session=Depends(get_session),
) -> CartService:
    return get_service(CartService, session)
```

### 新增實體時

**只需要：**

1. 創建 `core/repositories/order_repository.py`
2. 創建 `infra/db/repositories/order_repository_impl.py`
3. 創建 `core/services/order_service.py`

**無需修改 `wiring.py`！** 自動發現機制會自動處理。

## 範例：新增 Order 實體

### 之前（需要手寫）

```python
# infra/wiring.py
def create_order_repository(session: Session) -> OrderRepository:
    return OrderRepositoryImpl(session)

def create_order_service(session: Session) -> OrderService:
    repo = create_order_repository(session)
    return OrderService(order_repo=repo)
```

### 之後（自動化）

```python
# api/deps.py
def get_order_service(session=Depends(get_session)) -> OrderService:
    return get_service(OrderService, session)  # 自動處理所有依賴
```

## 複雜依賴範例

如果 Service 依賴多個 Repository：

```python
class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        payment_port: PaymentPort
    ):
        # ...
```

**無需手動組裝**，依賴解析器會自動：
1. 識別所有依賴類型
2. 自動創建對應實例
3. 注入到 Service

## 架構優勢

1. ✅ **消除重複代碼** - 無需為每個實體寫工廠函數
2. ✅ **自動發現** - 基於命名約定自動掃描
3. ✅ **自動解析** - 自動識別和注入依賴
4. ✅ **向後兼容** - 保留舊的工廠函數
5. ✅ **易於擴展** - 新增實體無需修改 wiring.py

## 技術細節

### 自動發現流程

1. 啟動時掃描 `core/repositories/` 目錄
2. 掃描 `infra/db/repositories/` 目錄
3. 基於命名約定建立映射：`CartRepository` → `CartRepositoryImpl`
4. 註冊到全局註冊表

### 依賴解析流程

1. 分析 Service 的 `__init__` 簽名
2. 提取參數類型和名稱
3. 對於每個依賴類型：
   - 如果是 `Session` → 直接使用
   - 如果是 `Repository` → 從註冊表獲取實作並創建
   - 如果是 `Port` → 未來擴展
4. 創建 Service 實例並注入所有依賴

## 注意事項

1. **命名約定必須嚴格遵守**：
   - Repository 接口：`{Entity}Repository`
   - Repository 實作：`{Entity}RepositoryImpl`
   - Service：`{Entity}Service`

2. **類型提示很重要**：
   - Service 的 `__init__` 必須有完整的類型提示
   - 依賴解析器依賴類型提示來識別依賴

3. **Session 注入**：
   - `Session` 類型會自動從參數中獲取
   - RepositoryImpl 的 `__init__` 必須接受 `session: Session` 參數

