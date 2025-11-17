# FastAPI Modular Backend

基於 Clean Architecture 原則實踐的 FastAPI 後端架構，提供模組化、可測試、易擴展的企業級後端解決方案。

---

## 📋 目錄

- [架構設計理念](#架構設計理念)
- [架構概況](#架構概況)
- [核心特性](#核心特性)
- [快速開始](#快速開始)
- [專案結構](#專案結構)
- [開發指南](#開發指南)
- [文檔](#文檔)

---

## 🏗️ 架構設計理念

本專案嚴格遵循以下架構原則與設計模式：

### Clean Architecture

採用 Robert C. Martin (Uncle Bob) 提出的 Clean Architecture 原則：
![claen-architecture.png](docs%2Fclaen-architecture.png)
> **圖片說明：** Clean Architecture 的同心圓分層架構，展示了依賴方向與控制流程。

- **依賴倒置原則（Dependency Inversion）**：高層模組不依賴低層模組，兩者都依賴抽象
- **開放封閉原則（Open/Closed）**：對擴展開放，對修改封閉
- **單一職責原則（Single Responsibility）**：每個模組、類別都有明確的單一職責
- **接口隔離原則（Interface Segregation）**：使用抽象接口定義契約，具體實現與使用方解耦

### Domain-Driven Design (DDD)

實踐 DDD 的核心概念：

- **聚合根（Aggregate Root）**：以業務聚合為單位組織領域模型
- **值對象（Value Object）**：不可變的值類型，通過值比較相等性
- **實體（Entity）**：具有唯一標識符的可變對象
- **領域服務（Domain Service）**：處理不屬於單一實體的業務邏輯
- **倉儲模式（Repository Pattern）**：抽象數據訪問層，隔離業務邏輯與數據存儲

### 架構分層

```
┌─────────────────────────────────────────┐
│        Domain Layer (Core)              │  ← 領域模型（圓心）
│  - Entities, Value Objects, Rules       │
│                                         │
│       ↑ 依賴方向（外層依賴內層）            │
├─────────────────────────────────────────┤
│       Application Layer (Use Cases)     │  ← Service 層
│  - Business Logic, Workflows            │
│                                         │
│       ↑ 依賴方向（外層依賴內層）            │
├─────────────────────────────────────────┤
│         API Layer (Interface)           │  ← HTTP/WebSocket/GraphQL
│  - Routes, Schemas, Converters          │
│                                         │
│       ↑ 依賴方向（外層依賴內層）            │
├─────────────────────────────────────────┤
│     Infrastructure Layer (Details)      │  ← 具體實現（最外層）
│  - Database, Cache, External Services   │
└─────────────────────────────────────────┘

依賴方向：外層 → 內層（從下往上指向圓心）
Domain 層不依賴任何外層，是最純粹的業務邏輯
```

---

## 🎯 架構概況

### 核心層級結構

```
src/app/
├── api/                          # API 層（Interface Adapters）
│   ├── http_app.py              # HTTP API 應用
│   ├── factory.py               # API 工廠（支援多種 API 類型）
│   ├── schemas/                 # Request/Response Schema
│   │   └── cart.py
│   ├── utils/
│   │   └── converters/          # Domain → API Schema 轉換器
│   │       └── cart.py
│   ├── carts.py                 # 路由處理
│   └── deps.py                  # FastAPI 依賴注入
│
├── core/                        # 核心層（Business Logic）
│   ├── domain/                  # 領域模型（純業務邏輯，無外部依賴）
│   │   ├── cart.py             # 簡單聚合（單一檔案）
│   │   └── order/              # 複雜聚合（子目錄）
│   │       ├── order.py        # 聚合根
│   │       ├── order_item.py   # 實體
│   │       ├── order_status.py # 枚舉
│   │       └── shipping_address.py  # 值對象
│   │
│   ├── repositories/            # Repository 抽象接口
│   │   └── cart_repository.py
│   │
│   └── services/                # 業務邏輯服務
│       └── cart_service.py
│
├── infra/                       # 基礎設施層（Implementation Details）
│   ├── db/                      # 數據庫相關
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   │   └── cart_item.py
│   │   ├── repositories/       # Repository 具體實現
│   │   │   ├── base_repository.py
│   │   │   └── cart_repository_impl.py
│   │   ├── migrations/         # Alembic 數據庫遷移
│   │   └── session.py          # 數據庫會話管理
│   │
│   ├── cache/                   # 緩存（Redis）
│   │   └── redis_client.py
│   │
│   └── wiring/                  # 自動化依賴注入
│       ├── auto_discovery.py   # 自動發現機制
│       ├── registry.py         # 依賴注冊表
│       ├── dependency_resolver.py  # 依賴解析器
│       └── factories.py        # 泛型工廠
│
├── application/                 # 應用初始化
│   └── app.py                  # 應用創建入口
│
└── config.py                    # 配置管理
```

### 數據流向

```
HTTP Request
    ↓
[API Layer] 路由處理
    ↓ (依賴注入)
[Service Layer] 業務邏輯
    ↓ (使用 Repository 接口)
[Domain Layer] 領域模型
    ↓ (通過 Repository 實現)
[Infrastructure Layer] 數據庫/緩存
    ↓
返回 Domain Model
    ↓ (Converter 轉換)
返回 API Schema
    ↓
HTTP Response
```

### 自動化依賴注入機制

基於**命名約定**的自動發現與注入：

```python
# 1. 定義 Repository 接口（core/repositories/cart_repository.py）
class CartRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        pass

# 2. 實現 Repository（infra/db/repositories/cart_repository_impl.py）
class CartRepositoryImpl(SqlAlchemyRepositoryBase, CartRepository):
    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        # 實現邏輯
        pass

# 3. 定義 Service（core/services/cart_service.py）
class CartService:
    def __init__(self, cart_repo: CartRepository):
        self.cart_repo = cart_repo

# 4. 在 API 層使用（api/deps.py）
def get_cart_service(session=Depends(get_session)) -> CartService:
    return get_service(CartService, session)  # 自動解析並注入依賴！
```

**無需手動配置！** Wiring 模組會自動：
1. 掃描 `core/repositories/` 找到所有 Repository 接口
2. 掃描 `infra/db/repositories/` 找到所有實現類
3. 基於命名約定建立映射（`CartRepository` → `CartRepositoryImpl`）
4. 自動解析 Service 的依賴並注入

---

## 核心特性

### 1. 模組化架構
- 清晰的層級分離
- 每層職責明確
- 易於理解和維護

### 2. 自動化依賴注入
- 基於命名約定的自動發現
- 無需手動配置
- 新增實體時零配置

### 3. 多 API 類型支援
- HTTP REST API（預設）
- WebSocket（可擴展）
- GraphQL（可擴展）
- 通過環境變數動態選擇

### 4. 靈活的領域模型組織
- 簡單聚合：單一檔案
- 複雜聚合：子目錄組織
- 支援平滑遷移

### 5. 完整的轉換層
- Domain Model → API Schema
- ORM Model → Domain Model
- 保持各層純粹性

### 6. 企業級特性
- 資料庫遷移（Alembic）
- Redis 緩存支援
- 容器化部署（Docker）
- 多服務角色支援（API, Worker, CLI）

---

## 🚀 快速開始

### 前置需求

- **Docker** & **Docker Compose**
- **Python 3.11+**（本地開發）
- **uv**（Python 包管理工具）

### 安裝 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 啟動專案

#### 方式一：使用開發腳本（推薦）

```bash
# 啟動所有服務
./scripts/dev-up.sh

# 關閉所有服務
./scripts/dev-down.sh
```

#### 方式二：使用 Docker Compose

```bash
# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f app

# 停止服務
docker-compose down
```

### 驗證服務

```bash
# 檢查健康狀態
curl http://localhost:8000/health

# 查看 API 文檔
open http://localhost:8000/docs

# 測試 API
curl -X POST http://localhost:8000/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "product_id": "prod456",
    "quantity": 2,
    "unit_price": 1000
  }'
```

### 服務端口
- **HTTP API**: `http://localhost:8000`
- **API 文檔**: `http://localhost:8000/docs`

---

## 📁 專案結構

```
fastapi_modular_backend/
├── src/app/                # 應用源碼
│   ├── api/               # API 層
│   ├── core/              # 核心層（Domain + Services）
│   ├── infra/             # 基礎設施層
│   ├── application/       # 應用初始化
│   ├── cli/               # CLI 命令
│   ├── worker/            # 背景任務（Celery）
│   └── config.py          # 配置
│
├── docs/                   # 架構文檔
│   ├── 架構說明.md
│   ├── API 層架構設計.md
│   ├── Domain 層組織規範.md
│   ├── Wiring 模組-自動化依賴注入.md
│   ├── 依賴注入流程詳解.md
│   └── 新增功能指南-User CRUD-*.md
│
├── docker/                 # Docker 配置
│   └── app/
│       ├── Dockerfile
│       └── entrypoint.sh
│
├── scripts/                # 開發腳本
│   ├── dev-up.sh          # 啟動開發環境
│   └── dev-down.sh        # 關閉開發環境
│
├── alembic.ini            # 資料庫遷移配置
├── docker-compose.yml     # Docker Compose 配置
├── pyproject.toml         # Python 專案配置
└── README.md              # 本文件
```

---

## 📖 開發指南

### 新增功能（以 User CRUD 為例）

#### 1. 建立 Domain 模型

```python
# core/domain/user.py
@dataclass
class User:
    id: Optional[int] = None
    email: str = ""
    name: str = ""
    created_at: Optional[datetime] = None
```

#### 2. 定義 Repository 接口

```python
# core/repositories/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User:
        raise NotImplementedError
```

#### 3. 實現 Repository

```python
# infra/db/repositories/user_repository_impl.py
class UserRepositoryImpl(SqlAlchemyRepositoryBase, UserRepository):
    def create(self, user: User) -> User:
        # 實現邏輯
        pass
```

#### 4. 建立 Service

```python
# core/services/user_service.py
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def create_user(self, email: str, name: str) -> User:
        # 業務邏輯
        pass
```

#### 5. 定義 API Schema

```python
# api/schemas/user.py
class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
```

#### 6. 建立 Converter

```python
# api/utils/converters/user.py
def user_out_from_domain(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )
```

#### 7. 實現 API 路由

```python
# api/users.py
@router.post("/users", response_model=UserOut)
def create_user(
    body: UserCreateIn,
    service: UserService = Depends(get_user_service),
) -> UserOut:
    user = service.create_user(email=body.email, name=body.name)
    return user_out_from_domain(user)
```

#### 8. 註冊依賴注入

```python
# api/deps.py
def get_user_service(session=Depends(get_session)) -> UserService:
    return get_service(UserService, session)  # 自動注入！
```

**完成！** 無需修改任何配置，Wiring 模組會自動處理所有依賴。

### 資料庫遷移

```bash
# 建立遷移
uv run alembic revision --autogenerate -m "add users table"

# 執行遷移
uv run alembic upgrade head

# 回滾遷移
uv run alembic downgrade -1
```

### 環境配置

通過環境變數配置應用：

```bash
# API 類型（http, websocket, graphql）
API_TYPE=http

# 服務角色（api, worker, cli）
SERVICE_ROLE=api

# 資料庫
DATABASE_URL=postgresql+psycopg://user:pass@host:port/db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 運行環境
ENVIRONMENT=development  # 或 production
RUN_MIGRATIONS=0         # 是否自動運行遷移
```


## 📚 文檔

詳細文檔請參考 `docs/` 目錄：

### 架構設計
- [架構說明.md](docs/架構說明.md) - 整體架構概述
- [API 層架構設計.md](docs/API%20層架構設計.md) - API 層設計規範
- [Domain 層組織規範.md](docs/Domain%20層組織規範.md) - 領域模型組織方式
- [Repository 層轉換模式說明.md](docs/Repository%20層轉換模式說明.md) - 資料轉換模式

### 核心機制
- [Wiring 模組-自動化依賴注入.md](docs/Wiring%20模組-自動化依賴注入.md) - 自動依賴注入機制
- [依賴注入流程詳解.md](docs/依賴注入流程詳解.md) - 依賴注入完整流程
- [多 API 創建問題分析與解決方案.md](docs/多%20API%20創建問題分析與解決方案.md) - API 工廠模式

### 開發指南
- [新增功能指南-User CRUD-01-基礎架構.md](docs/新增功能指南-User%20CRUD-01-基礎架構.md)
- [新增功能指南-User CRUD-02-Create.md](docs/新增功能指南-User%20CRUD-02-Create.md)
- [新增功能指南-User CRUD-03-Retrieve.md](docs/新增功能指南-User%20CRUD-03-Retrieve.md)
- [新增功能指南-User CRUD-04-Update.md](docs/新增功能指南-User%20CRUD-04-Update.md)
- [新增功能指南-User CRUD-05-Delete.md](docs/新增功能指南-User%20CRUD-05-Delete.md)

### 進階主題
- [Domain 層遷移指南.md](docs/Domain%20層遷移指南.md) - 簡單聚合到複雜聚合遷移
- [WebSocket 架構方案分析.md](docs/WebSocket%20架構方案分析.md) - WebSocket 支援方案

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

### 開發流程

1. Fork 本專案
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 📝 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

---

## 🙏 致謝

本專案的架構設計參考了以下資源：

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) by Robert C. Martin
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html) by Eric Evans
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python Web Framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL Toolkit and ORM

---

<div align="center">
  <p>如有問題或建議，歡迎開 Issue 討論！</p>
  <p>⭐ 如果這個專案對你有幫助，請給個星星支持一下！</p>
</div>
