# IoC Container 模組（dependency-injector）

> **注意：** 本專案已以 `infra/containers/` 取代舊的 `infra/wiring/` 自動發現機制。本文描述現行架構。

## 概述

使用 [dependency-injector](https://python-dependency-injector.ets-labs.org/) 的 **DeclarativeContainer** 集中管理依賴圖，取代反射式自動發現。新增實體時在 Container 中明確註冊 Provider，換取可視化的依賴關係與穩定的測試覆寫。

## 目錄結構

```
infra/containers/
├── __init__.py          # get_container()、init/shutdown hooks
├── application.py       # ApplicationContainer（根容器）
├── infrastructure.py    # 引擎、Redis、session Resource
├── repositories.py      # Repository Factory
└── services.py          # Service Factory
```

## 容器分層

| 容器 | Provider 類型 | 管理對象 |
|---|---|---|
| `InfrastructureContainer` | Singleton / Resource | `db_engine`、`session_factory`、`redis`、`db_session` |
| `RepositoryContainer` | Factory | `CartRepositoryImpl`（綁定 request-scoped `Session`） |
| `ServiceContainer` | Factory | `CartService` |
| `ApplicationContainer` | Container 巢狀組裝 | 以上三層 |

## 使用方式

### HTTP（FastAPI）

```python
# api/deps.py
def inject_service(provider: providers.Factory[T]) -> Callable[..., T]:
    def _dependency(session: Session = Depends(get_session)) -> T:
        return provider(session=session)
    return _dependency

# api/carts.py
from app.infra.containers import get_container

CartServiceDep = Annotated[
    CartService,
    Depends(inject_service(get_container().services.cart_service)),
]
```

`get_session` 是唯一保留 `Depends` 的 HTTP 專用依賴，負責請求級 DB session 生命週期。

### Celery / CLI / 測試腳本

```python
from app.infra.containers import get_container

container = get_container()

# 方式 1：自行管理 session
session = container.infra.session_factory()()
try:
    service = container.services.cart_service(session=session)
    service.add_item(...)
    session.commit()
finally:
    session.close()

# 方式 2：Resource（推薦給腳本）
with container.infra.db_session() as session:
    service = container.services.cart_service(session=session)
```

### 測試覆寫

```python
with container.services.cart_service.override(providers.Object(stub_service)):
    response = client.get("/api/cart?user_id=1")
```

執行測試請使用標準 Docker 流程：`./scripts/test.sh`（詳見 [測試流程說明](測試流程說明.md)）。

## 新增實體標準流程（以 User 為例）

1. `core/repositories/user_repository.py` — 介面
2. `infra/db/repositories/user_repository_impl.py` — 實作
3. `core/services/user_service.py` — 用例
4. `infra/containers/repositories.py` — 加 `user_repository = providers.Factory(...)`
5. `infra/containers/services.py` — 加 `user_service = providers.Factory(...)`
6. `api/users.py` — `UserServiceDep = Annotated[..., Depends(inject_service(get_container().services.user_service))]`

## 架構優勢

1. **集中可見** — 所有依賴關係在 Container 檔案中一目了然
2. **Scope 明確** — Singleton（基礎設施）vs Factory（業務物件）
3. **脫離 HTTP** — 非 HTTP 入口直接 `container.services.xxx(session=...)`
4. **穩定測試** — `container.override()` 不依賴函式位址
5. **簽名乾淨** — 不使用 `Provide[]` + wiring，路由維持 `CartServiceDep` 模式

## 啟動與生命週期

```python
# application/app.py
container = init_container()
app.state.container = container

@app.on_event("shutdown")
def _shutdown_container():
    shutdown_container()
```

`session.py` 與 `redis_client.py` 透過 `get_container().infra` 取得 Singleton 資源。
