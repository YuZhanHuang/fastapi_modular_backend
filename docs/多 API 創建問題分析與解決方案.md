# 多 API 創建問題分析與解決方案

## 問題描述

### 當前狀況

在 `application/app.py` 中，直接導入並調用具體的 API 創建函數：

```python
from app.api.http_app import create_http_app

def create_app(...) -> FastAPI:
    # ...
    app = create_http_app()  # 直接依賴具體實現
    return app
```

### 問題場景

假設未來需要支援多種 API 類型（REST、GraphQL、WebSocket、gRPC 等），會出現以下問題：

```python
# 未來可能的場景（問題版本）
from app.api.http_app import create_http_app          # REST API
from app.api.graphql_app import create_graphql_app    # GraphQL API
from app.api.websocket_app import create_websocket_app # WebSocket API
from app.api.grpc_app import create_grpc_app          # gRPC API

def create_app(..., api_type: str = "http") -> FastAPI:
    # 需要根據配置選擇創建哪個 API？
    if api_type == "rest":
        app = create_http_app()
    elif api_type == "graphql":
        app = create_graphql_app()
    elif api_type == "websocket":
        app = create_websocket_app()
    elif api_type == "grpc":
        app = create_grpc_app()
    # ... 越來越多的 if-elif
    
    return app
```

**問題：**
- 每次新增 API 類型都需要修改 `application/app.py`
- 違反開放封閉原則（對擴展開放，對修改封閉）
- `application` 層需要知道所有 API 類型的細節

---

## 根本原因分析

### 1. 違反依賴倒置原則（Dependency Inversion Principle）

**原則：**
- 高層模組不應該依賴低層模組，兩者都應該依賴抽象
- 抽象不應該依賴細節，細節應該依賴抽象

**當前問題：**
```
application/app.py (高層) → api/http_app.py (低層具體實現)
```

`application` 層直接依賴 `api` 層的具體實現，而不是抽象接口。

**應該：**
```
application/app.py → api/ (抽象接口) → api/http_app.py (具體實現)
```

### 2. 違反開放封閉原則（Open/Closed Principle）

**原則：**
- 對擴展開放：可以新增功能
- 對修改封閉：不需要修改現有代碼

**當前問題：**
- ✅ 可以新增 API 類型（擴展）
- ❌ 但必須修改 `application/app.py`（違反封閉原則）

**影響：**
- 每次新增 API 類型都需要修改核心應用初始化代碼
- 增加測試負擔（需要測試所有分支）
- 容易引入錯誤

### 3. 職責不清

**`application` 層的職責應該是：**
- ✅ 初始化基礎設施（資料庫、Redis 等）
- ✅ 組裝應用程式組件
- ✅ 提供統一的應用創建入口

**不應該是：**
- ❌ 決定創建哪種 API 類型
- ❌ 知道具體有哪些 API 實現
- ❌ 處理 API 類型的選擇邏輯

### 4. 缺乏統一抽象

**問題：**
- 每個 API 類型都是獨立的函數，沒有共同契約
- 沒有統一的接口來創建不同類型的 API
- 無法統一管理和配置

**影響：**
- 無法統一處理 API 創建邏輯
- 無法統一配置和監控
- 擴展困難

---

## 解決方案

### 方案一：統一 API 創建接口

**概念：**
創建統一的抽象接口，讓 `application` 層只依賴抽象。

**實作：**

```python
# api/__init__.py 或 api/factory.py
from typing import Protocol
from fastapi import FastAPI

class APIAppFactory(Protocol):
    """API 應用創建工廠協議"""
    def create() -> FastAPI:
        """創建並返回 API 應用實例"""
        ...

def create_api_app(api_type: str = "http") -> FastAPI:
    """
    統一的 API 應用創建入口
    
    :param api_type: API 類型（"http", "graphql", "websocket" 等）
    :return: FastAPI 應用實例
    """
    factories = {
        "http": lambda: __import__("app.api.http_app").api.http_app.create_http_app(),
        # 未來可以擴展：
        # "graphql": lambda: __import__("app.api.graphql_app").api.graphql_app.create_graphql_app(),
        # "websocket": lambda: __import__("app.api.websocket_app").api.websocket_app.create_websocket_app(),
    }
    
    factory = factories.get(api_type)
    if not factory:
        raise ValueError(f"Unknown API type: {api_type}")
    
    return factory()
```

**優點：**
- ✅ 統一接口
- ✅ 簡單直接

**缺點：**
- ❌ 仍然需要修改 `create_api_app` 函數來新增類型
- ❌ 使用動態導入，不夠優雅

---

### 方案二：配置驅動

**概念：**
通過配置決定要創建哪些 API，支援同時創建多個 API。

**實作：**

```python
# application/app.py
def create_app(
    init_db: Optional[bool] = None,
    create_tables: bool = False,
    api_types: Optional[List[str]] = None,  # 新增參數
) -> FastAPI:
    """
    創建並初始化應用程式
    
    :param api_types: 要創建的 API 類型列表，預設為 ["http"]
    """
    # ...
    
    if api_types is None:
        api_types = os.getenv("API_TYPES", "http").split(",")
    
    # 可以創建多個 API 應用（如果需要）
    apps = []
    for api_type in api_types:
        app = create_api_app(api_type.strip())
        apps.append(app)
    
    # 返回主要應用（或合併多個應用）
    return apps[0] if len(apps) == 1 else merge_apps(apps)
```

**優點：**
- ✅ 支援多個 API 同時運行
- ✅ 配置靈活

**缺點：**
- ❌ 需要處理多個應用的合併邏輯
- ❌ 複雜度較高

---

### 方案三：工廠模式（推薦）⭐

**概念：**
創建專門的工廠模組，使用註冊機制管理所有 API 創建函數。

**實作：**

```python
# api/factory.py
"""
API 應用工廠

統一管理所有 API 類型的創建邏輯，支援動態註冊和擴展。
"""
from typing import Dict, Callable
from fastapi import FastAPI
import os


class APIAppFactory:
    """API 應用工廠"""
    
    _factories: Dict[str, Callable[[], FastAPI]] = {}
    
    @classmethod
    def register(cls, api_type: str, factory: Callable[[], FastAPI]):
        """
        註冊 API 創建工廠
        
        :param api_type: API 類型名稱（如 "http", "graphql"）
        :param factory: 創建函數，應返回 FastAPI 實例
        """
        cls._factories[api_type] = factory
    
    @classmethod
    def create(cls, api_type: Optional[str] = None) -> FastAPI:
        """
        創建 API 應用
        
        :param api_type: API 類型，如果為 None 則從環境變數讀取
        :return: FastAPI 應用實例
        :raises ValueError: 如果 API 類型不存在
        """
        if api_type is None:
            api_type = os.getenv("API_TYPE", "http")
        
        factory = cls._factories.get(api_type)
        if not factory:
            available = list(cls._factories.keys())
            raise ValueError(
                f"Unknown API type: {api_type}. "
                f"Available types: {available}"
            )
        
        return factory()
    
    @classmethod
    def get_available_types(cls) -> list[str]:
        """獲取所有已註冊的 API 類型"""
        return list(cls._factories.keys())


# 註冊 HTTP API（預設）
from app.api.http_app import create_http_app
APIAppFactory.register("http", create_http_app)

# 未來註冊其他 API 時，只需在這裡添加：
# from app.api.graphql_app import create_graphql_app
# APIAppFactory.register("graphql", create_graphql_app)
```

```python
# application/app.py
from app.api.factory import APIAppFactory

def create_app(
    init_db: Optional[bool] = None,
    create_tables: bool = False,
    api_type: Optional[str] = None,  # 可選參數
) -> FastAPI:
    """
    創建並初始化應用程式
    
    :param api_type: API 類型，如果為 None 則從環境變數讀取
    :return: FastAPI 應用實例
    """
    # 初始化基礎設施
    if init_db is None:
        is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
        run_migrations = os.getenv("RUN_MIGRATIONS", "1") == "1"
        init_db = not is_production and not run_migrations
    
    if init_db:
        init_database(create_tables=create_tables)
    
    # 使用工廠創建 API 應用
    app = APIAppFactory.create(api_type)
    
    return app
```

**優點：**
- ✅ **符合依賴倒置原則**：`application` 層只依賴 `APIAppFactory` 抽象
- ✅ **符合開放封閉原則**：新增 API 類型只需註冊，無需修改 `application/app.py`
- ✅ **職責清晰**：工廠負責管理 API 創建，`application` 層只負責組裝
- ✅ **配置靈活**：可通過環境變數或參數選擇 API 類型
- ✅ **易於測試**：可以輕鬆註冊 mock 工廠進行測試
- ✅ **易於擴展**：新增 API 類型只需兩行代碼

**缺點：**
- ⚠️ 需要額外的工廠模組（但這是值得的抽象）

---

## 方案比較

| 面向 | 方案一（統一接口） | 方案二（配置驅動） | 方案三（工廠模式）⭐ |
|------|-------------------|-------------------|-------------------|
| **依賴倒置** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **開放封閉** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **職責分離** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **易於擴展** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **配置靈活** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **複雜度** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **可測試性** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 推薦方案：工廠模式

### 為什麼選擇工廠模式？

1. **符合 Clean Architecture 原則**
   - 依賴倒置：高層不依賴低層具體實現
   - 開放封閉：對擴展開放，對修改封閉

2. **易於擴展**
   - 新增 API 類型只需：
     1. 創建對應的 `api/{type}_app.py`
     2. 在工廠中註冊
     3. 無需修改 `application/app.py`

3. **職責清晰**
   - `api/factory.py`：負責管理 API 創建
   - `application/app.py`：負責應用組裝
   - 各司其職，互不干擾

4. **配置靈活**
   - 支援環境變數配置
   - 支援參數傳入
   - 支援動態選擇

---

## 實作範例

### 當前實作（問題版本）

```python
# application/app.py
from app.api.http_app import create_http_app  # 直接依賴具體實現

def create_app(...) -> FastAPI:
    app = create_http_app()  # 硬編碼
    return app
```

### 改進後實作（工廠模式）

```python
# api/factory.py
class APIAppFactory:
    _factories: Dict[str, Callable[[], FastAPI]] = {}
    
    @classmethod
    def register(cls, api_type: str, factory: Callable[[], FastAPI]):
        cls._factories[api_type] = factory
    
    @classmethod
    def create(cls, api_type: Optional[str] = None) -> FastAPI:
        if api_type is None:
            api_type = os.getenv("API_TYPE", "http")
        return cls._factories[api_type]()

# 註冊 HTTP API
from app.api.http_app import create_http_app
APIAppFactory.register("http", create_http_app)
```

```python
# application/app.py
from app.api.factory import APIAppFactory  # 只依賴抽象

def create_app(..., api_type: Optional[str] = None) -> FastAPI:
    # ...
    app = APIAppFactory.create(api_type)  # 通過工廠創建
    return app
```

### 未來擴展範例

假設未來需要新增 GraphQL API：

```python
# 1. 創建 GraphQL API 模組
# api/graphql_app.py
def create_graphql_app() -> FastAPI:
    # GraphQL 應用創建邏輯
    pass

# 2. 在工廠中註冊（只需這一步！）
# api/factory.py
from app.api.graphql_app import create_graphql_app
APIAppFactory.register("graphql", create_graphql_app)

# 3. 使用（無需修改 application/app.py）
# 通過環境變數或參數選擇
API_TYPE=graphql python -m uvicorn app.application.app:app
```

**無需修改 `application/app.py`！** ✅

---

## 使用方式

### 1. 預設使用（HTTP API）

```bash
# 環境變數未設置時，預設使用 HTTP API
uvicorn app.application.app:app
```

### 2. 通過環境變數選擇

```bash
# 使用 GraphQL API
API_TYPE=graphql uvicorn app.application.app:app

# 使用 WebSocket API
API_TYPE=websocket uvicorn app.application.app:app
```

### 3. 通過參數選擇（測試時）

```python
# 測試時可以傳入參數
app = create_app(api_type="graphql")
```

---

## 總結

### 問題根源

1. **違反依賴倒置原則**：高層直接依賴低層具體實現
2. **違反開放封閉原則**：新增功能需要修改現有代碼
3. **職責不清**：`application` 層承擔了不應該的職責
4. **缺乏統一抽象**：沒有統一的接口管理 API 創建

### 解決方案

**工廠模式**提供了：
- ✅ 統一的抽象接口
- ✅ 動態註冊機制
- ✅ 配置靈活性
- ✅ 易於擴展和測試

### 實作效果

**之前：**
- 新增 API 類型 → 修改 `application/app.py` ❌
- 違反開放封閉原則 ❌
- 職責不清 ❌

**之後：**
- 新增 API 類型 → 只需註冊 ✅
- 符合開放封閉原則 ✅
- 職責清晰 ✅

---

## 參考資料

- [SOLID 原則](https://en.wikipedia.org/wiki/SOLID)
- [依賴倒置原則](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [開放封閉原則](https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle)
- [工廠模式](https://en.wikipedia.org/wiki/Factory_method_pattern)

