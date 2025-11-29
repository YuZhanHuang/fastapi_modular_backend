# 連接池管理詳解：FastAPI 與 SQLAlchemy

## 概述

本文檔詳細說明 FastAPI 與 SQLAlchemy 中連接池的工作原理、配置方式與最佳實踐。

---

## 一、SQLAlchemy 連接池基礎

### 1.1 什麼是連接池？

**連接池（Connection Pool）** 是一組預先創建並保持打開狀態的資料庫連接。

**為什麼需要連接池？**

```
沒有連接池：
請求 1: 建立連接(50ms) → 查詢(10ms) → 關閉連接(5ms) = 65ms
請求 2: 建立連接(50ms) → 查詢(10ms) → 關閉連接(5ms) = 65ms
請求 3: 建立連接(50ms) → 查詢(10ms) → 關閉連接(5ms) = 65ms

有連接池：
請求 1: 從池取連接(0.1ms) → 查詢(10ms) → 歸還連接(0.1ms) = 10.2ms
請求 2: 從池取連接(0.1ms) → 查詢(10ms) → 歸還連接(0.1ms) = 10.2ms
請求 3: 從池取連接(0.1ms) → 查詢(10ms) → 歸還連接(0.1ms) = 10.2ms

性能提升：約 6 倍！
```

### 1.2 SQLAlchemy 的連接池類型

SQLAlchemy 支援多種連接池實現：

| 連接池類型 | 說明 | 適用場景 |
|-----------|------|---------|
| **QueuePool** | 默認，使用隊列管理連接 | 生產環境（推薦） |
| **NullPool** | 不使用連接池，每次創建新連接 | 開發環境、測試 |
| **StaticPool** | 始終返回同一個連接 | SQLite |
| **SingletonThreadPool** | 每個線程一個連接 | SQLite 多線程 |
| **AssertionPool** | 用於測試 | 測試環境 |

**預設行為：**
```python
# 使用 PostgreSQL、MySQL 時，默認使用 QueuePool
engine = create_engine("postgresql://...")  # 自動使用 QueuePool

# 使用 SQLite 時，默認使用 StaticPool
engine = create_engine("sqlite:///app.db")  # 自動使用 StaticPool
```

---

## 二、您當前的配置

### 2.1 當前實現

**檔案：`infra/db/session.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(
    settings.DATABASE_URL,  # "postgresql+psycopg://app:app@db:5432/app"
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()  # ← 從連接池獲取連接
    try:
        yield db
    finally:
        db.close()  # ← 歸還連接到連接池
```

### 2.2 默認連接池參數

**當前配置使用 SQLAlchemy 的默認值：**

| 參數 | 默認值 | 說明 |
|-----|-------|------|
| `pool_size` | 5 | 連接池中保持的連接數 |
| `max_overflow` | 10 | 超出 pool_size 後最多再創建的連接數 |
| `pool_timeout` | 30 秒 | 等待可用連接的超時時間 |
| `pool_recycle` | -1（不回收） | 連接回收時間（秒） |
| `pool_pre_ping` | False | 使用前是否檢查連接可用性 |

**實際行為：**
```
最小連接數：0（啟動時不創建）
初始連接數：5（第一批請求時創建）
最大連接數：15（pool_size + max_overflow = 5 + 10）
```

---

## 三、連接池的工作流程

### 3.1 完整的請求生命週期

```
[HTTP 請求到達]
    ↓
[FastAPI 路由匹配]
    ↓
[FastAPI Depends 觸發]
    ↓
1. 調用 get_session()
    ↓
2. SessionLocal() 創建 Session
    ↓
3. Session 向 Engine 請求連接
    ↓
4. Engine 從連接池獲取連接
    ├─ 如果池中有空閒連接 → 立即返回
    ├─ 如果池已滿但未達 max_overflow → 創建新連接
    └─ 如果已達最大連接數 → 等待（最多 pool_timeout 秒）
    ↓
5. 執行查詢（使用連接）
    ↓
6. 路由函數返回
    ↓
7. finally 塊執行 db.close()
    ↓
8. Session 關閉，連接歸還到連接池
    ↓
[HTTP 響應返回]
```

### 3.2 連接池的狀態變化

**場景：5 個並發請求**

```
初始狀態：
連接池：[] (空)
可用連接：0

請求 1 到達：
連接池：[創建連接1]
使用中：[連接1]
可用連接：0

請求 2 到達：
連接池：[連接1, 創建連接2]
使用中：[連接1, 連接2]
可用連接：0

... (請求 3, 4, 5 同理)

請求 1 完成：
連接池：[連接1(空閒), 連接2, 連接3, 連接4, 連接5]
使用中：[連接2, 連接3, 連接4, 連接5]
可用連接：1

請求 6 到達：
連接池：[連接1(使用中), 連接2, 連接3, 連接4, 連接5]
使用中：[連接1, 連接2, 連接3, 連接4, 連接5]
可用連接：0
行為：重用連接1（無需創建新連接）
```

### 3.3 超出連接池的情況

**場景：20 個並發請求（超過默認 15 個最大連接）**

```
前 5 個請求：
連接池：[連接1, 連接2, 連接3, 連接4, 連接5]
使用中：全部
狀態：正常

第 6-15 個請求：
連接池：[連接1-5(池內), 連接6-15(overflow)]
使用中：全部 15 個
狀態：達到 max_overflow

第 16-20 個請求：
狀態：阻塞等待
行為：等待前面的請求釋放連接（最多等待 30 秒）
如果超時：拋出 TimeoutError
```

---

## 四、關鍵概念詳解

### 4.1 Session vs Connection

**重要區別：**

```python
# Session（ORM 層）
session = SessionLocal()  # ← 這不是連接！
# Session 是 ORM 的工作單元，管理對象的狀態

# Connection（DBAPI 層）
connection = session.connection()  # ← 這才是真正的連接
# Connection 是底層的資料庫連接
```

**關係圖：**

```
HTTP 請求
    ↓
Session (ORM 層)
    ↓
Connection (DBAPI 層)
    ↓
連接池 (Pool)
    ↓
PostgreSQL 伺服器
```

### 4.2 Session.close() 不會關閉連接

**關鍵理解：**

```python
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # ← 這不會關閉連接！
```

**實際行為：**

```python
# db.close() 只做了這些事：
1. 清理 Session 的內部狀態
2. 將 Connection 歸還到連接池
3. Connection 保持打開狀態（在池中）

# 連接不會真正關閉，會被重用
```

### 4.3 連接的生命週期

```
連接創建：
    ↓
加入連接池（空閒狀態）
    ↓
被 Session 借用（使用中）
    ↓
Session.close() → 歸還到池（空閒狀態）
    ↓
被下一個 Session 借用（使用中）
    ↓
... 重複使用 ...
    ↓
超過 pool_recycle 時間 → 關閉並移除
或
應用關閉 → engine.dispose() → 關閉所有連接
```

---

## 五、連接池配置詳解

### 5.1 核心參數

#### `pool_size`（連接池大小）

**定義：** 連接池中保持的連接數量

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # 保持 20 個連接
)
```

**如何選擇？**

```
公式：pool_size = (CPU 核心數 × 2) + 1

範例：
- 4 核 CPU：(4 × 2) + 1 = 9
- 8 核 CPU：(8 × 2) + 1 = 17

但也要考慮：
- 應用實例數量
- 資料庫最大連接數限制
- 預期的並發請求量
```

**實際建議：**

| 場景 | pool_size | 理由 |
|-----|-----------|------|
| 開發環境 | 5 | 並發低 |
| 小型應用 | 10-20 | 適度並發 |
| 中型應用 | 20-50 | 較高並發 |
| 大型應用 | 50-100 | 高並發 |

**注意事項：**

```
❌ 過小：
- 請求會頻繁等待
- 響應時間增加

❌ 過大：
- 浪費資源（連接空閒）
- 資料庫壓力大
- 可能超過資料庫連接數限制

✅ 合適：
- 根據實際並發量調整
- 通過監控和壓力測試確定
```

#### `max_overflow`（溢出連接數）

**定義：** 超出 pool_size 後，最多再創建的臨時連接數

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,  # 最多再創建 20 個臨時連接
)

# 最大總連接數 = 10 + 20 = 30
```

**溢出連接的特性：**

```
池內連接（pool_size）：
- 長期存在
- 使用完歸還到池中
- 可以被重用

溢出連接（overflow）：
- 臨時創建
- 使用完立即關閉
- 不會留在池中
```

**使用場景：**

```
正常情況：使用 pool_size 的連接
突發流量：臨時創建 overflow 連接

範例：
平時 QPS 100：pool_size=10 足夠
突發 QPS 300：需要 overflow 額外支援
```

**如何選擇？**

```
保守：max_overflow = pool_size（1:1）
範例：pool_size=10, max_overflow=10 → 最大 20 個連接

激進：max_overflow = pool_size × 2（1:2）
範例：pool_size=10, max_overflow=20 → 最大 30 個連接

極端：max_overflow = 0（不允許溢出）
範例：pool_size=10, max_overflow=0 → 最大 10 個連接
```

#### `pool_timeout`（等待超時）

**定義：** 等待可用連接的最長時間（秒）

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,  # 等待 30 秒
)
```

**行為：**

```
請求到達時：
1. 嘗試從池中獲取連接
2. 如果沒有可用連接且未達 max_overflow → 創建新連接
3. 如果已達最大連接數 → 等待（最多 pool_timeout 秒）
4. 如果超時 → 拋出 TimeoutError

範例：
最大 20 個連接，目前全部使用中
第 21 個請求：等待 30 秒
- 如果 30 秒內有連接釋放 → 使用該連接
- 如果 30 秒後仍無可用連接 → TimeoutError
```

**如何選擇？**

```
快速失敗：pool_timeout=5-10 秒
- 適合高 QPS 應用
- 快速返回錯誤，避免請求堆積

正常：pool_timeout=30 秒（默認）
- 適合中等 QPS 應用
- 平衡等待時間和成功率

寬容：pool_timeout=60 秒或更長
- 適合低 QPS 應用
- 盡可能等待連接可用
```

#### `pool_recycle`（連接回收時間）

**定義：** 連接在池中的最大存活時間（秒）

```python
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,  # 1 小時後回收連接
)
```

**為什麼需要回收？**

```
問題：
資料庫會自動關閉長時間空閒的連接
範例：MySQL 默認 8 小時（wait_timeout）

如果不回收：
1. 連接在池中超過 8 小時
2. 資料庫端已關閉連接
3. 應用端嘗試使用 → 錯誤！

解決方案：
定期回收連接，確保連接有效
```

**如何選擇？**

```
MySQL：pool_recycle=3600（1 小時）
理由：wait_timeout 默認 8 小時，提前回收

PostgreSQL：pool_recycle=7200（2 小時）
理由：PostgreSQL 連接更穩定

通用建議：
pool_recycle = 資料庫超時時間 × 0.5
範例：資料庫超時 8 小時 → pool_recycle=14400 秒（4 小時）
```

#### `pool_pre_ping`（連接健康檢查）

**定義：** 使用連接前先檢查是否有效

```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 啟用健康檢查
)
```

**行為：**

```
pool_pre_ping=False（默認）：
1. 從池中取出連接
2. 直接使用
3. 如果連接已失效 → 查詢失敗 → 錯誤

pool_pre_ping=True：
1. 從池中取出連接
2. 發送簡單查詢（SELECT 1）
3. 如果連接失效 → 創建新連接
4. 使用有效連接
```

**優缺點：**

```
優點：
✅ 避免使用失效連接
✅ 提高查詢成功率
✅ 應對網絡不穩定

缺點：
❌ 每次使用前都要額外查詢（SELECT 1）
❌ 輕微性能開銷（約 0.1-1ms）
```

**建議：**

```
推薦啟用：
- 生產環境（連接穩定性優先）
- 網絡不穩定的環境
- 資料庫會自動關閉連接

可以不啟用：
- 開發環境（性能優先）
- 網絡非常穩定
- 已正確配置 pool_recycle
```

---

## 六、推薦配置

### 6.1 開發環境配置

```python
# infra/db/session.py
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=True,  # 顯示 SQL（開發時很有用）
    pool_size=5,  # 開發環境並發低
    max_overflow=5,
    pool_timeout=10,
    pool_recycle=3600,  # 1 小時
    pool_pre_ping=False,  # 開發環境可以不檢查
)
```

### 6.2 生產環境配置（小型應用）

```python
# infra/db/session.py
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,  # 生產環境不顯示 SQL
    pool_size=20,  # 中等並發
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,  # 1 小時
    pool_pre_ping=True,  # 生產環境建議啟用
)
```

### 6.3 生產環境配置（大型應用）

```python
# infra/db/session.py
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_size=50,  # 高並發
    max_overflow=20,
    pool_timeout=10,  # 快速失敗
    pool_recycle=3600,
    pool_pre_ping=True,
    # 額外參數
    connect_args={
        "connect_timeout": 10,  # 連接超時
        "options": "-c statement_timeout=30000",  # 查詢超時 30 秒（PostgreSQL）
    }
)
```

### 6.4 根據環境動態配置

```python
# config.py
class Settings(BaseSettings):
    DATABASE_URL: str
    
    # 連接池配置
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = False
    
    class Config:
        env_file = ".env"

# infra/db/session.py
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
)
```

**環境變數配置：**

```bash
# .env.dev
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_TIMEOUT=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=false

# .env.prod
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
```

---

## 七、常見問題與解決方案

### 7.1 連接池耗盡（Pool Timeout）

**錯誤訊息：**
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, 
connection timed out, timeout 30
```

**原因：**
```
並發請求 > (pool_size + max_overflow)
且請求處理時間長
```

**解決方案：**

```python
# 方案 1：增加連接池大小
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # 從 5 增加到 20
    max_overflow=10,
)

# 方案 2：減少請求處理時間
# - 優化資料庫查詢
# - 添加索引
# - 使用快取

# 方案 3：水平擴展
# - 增加應用實例數量
# - 使用負載均衡
```

### 7.2 連接洩漏（Connection Leak）

**症狀：**
```
連接數持續增加
最終耗盡連接池
應用無法響應
```

**原因：**
```python
# 錯誤示例：Session 沒有正確關閉
def bad_example():
    session = SessionLocal()
    # 忘記關閉 session
    return session.query(User).all()
    # Session 沒有關閉，連接永遠不歸還
```

**解決方案：**

```python
# 方案 1：使用 try-finally（當前方案）✅
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 保證一定會關閉

# 方案 2：使用 context manager
from contextlib import contextmanager

@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# 使用
with get_db_session() as session:
    session.query(User).all()
```

### 7.3 連接已斷開（Connection Lost）

**錯誤訊息：**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) 
server closed the connection unexpectedly
```

**原因：**
```
連接在池中太久
資料庫端已關閉連接
應用端不知道
```

**解決方案：**

```python
# 方案 1：啟用 pool_pre_ping（推薦）✅
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 使用前檢查連接
)

# 方案 2：設置 pool_recycle
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,  # 1 小時回收一次
)

# 方案 3：兩者結合（最佳）
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### 7.4 資料庫連接數限制

**錯誤訊息：**
```
psycopg2.OperationalError: FATAL: remaining connection slots are reserved
```

**原因：**
```
所有應用實例的連接數總和超過資料庫限制

範例：
PostgreSQL max_connections=100
應用實例：5 個
每個實例 pool_size=20, max_overflow=10
總連接數：5 × (20 + 10) = 150 > 100（超過限制）
```

**解決方案：**

```python
# 方案 1：計算合適的連接池大小
資料庫最大連接數：100
保留給管理員：10
可用連接數：90
應用實例數：5
每個實例最大連接：90 ÷ 5 = 18

# 配置
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 正常使用 10 個
    max_overflow=8,  # 最多再 8 個 = 總共 18 個
)

# 方案 2：增加資料庫連接數限制
# PostgreSQL：修改 postgresql.conf
max_connections = 200

# 方案 3：使用連接池代理（PgBouncer）
# 應用 → PgBouncer → PostgreSQL
# PgBouncer 可以管理數千個應用連接到少量資料庫連接
```

---

## 八、監控與診斷

### 8.1 監控連接池狀態

```python
# 獲取連接池狀態
def get_pool_status():
    pool = engine.pool
    return {
        "size": pool.size(),  # 當前連接數
        "checked_in": pool.checkedin(),  # 空閒連接數
        "checked_out": pool.checkedout(),  # 使用中連接數
        "overflow": pool.overflow(),  # 溢出連接數
        "total": pool.size() + pool.overflow(),  # 總連接數
    }

# 在監控端點中使用
@app.get("/health/db")
def database_health():
    status = get_pool_status()
    return {
        "status": "healthy",
        "pool": status,
    }
```

### 8.2 連接池指標

**關鍵指標：**

```python
# 1. 連接使用率
connection_usage = checked_out / (pool_size + max_overflow)

# 2. 連接等待次數
# 需要自定義追蹤

# 3. 連接創建次數
# 需要自定義追蹤

# 4. 平均連接等待時間
# 需要自定義追蹤
```

### 8.3 日誌記錄

```python
import logging

# 啟用 SQLAlchemy 連接池日誌
logging.basicConfig()
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

# 會輸出：
# Pool started
# Pool connection added
# Pool connection removed
# Connection <xxx> checked out from pool
# Connection <xxx> returned to pool
```

---

## 九、最佳實踐總結

### 9.1 配置原則

```
1. 從保守配置開始
   pool_size=10, max_overflow=10

2. 通過監控收集數據
   - 連接使用率
   - P95/P99 延遲
   - 連接等待次數

3. 根據數據調整
   - 使用率 > 80%：增加 pool_size
   - 頻繁等待：增加 max_overflow
   - 使用率 < 30%：減少 pool_size

4. 考慮資料庫限制
   所有實例總連接數 < 資料庫最大連接數 × 0.8
```

### 9.2 生產環境檢查清單

- [ ] ✅ 設置合適的 `pool_size`（根據並發量）
- [ ] ✅ 設置合理的 `max_overflow`（pool_size 的 0.5-1 倍）
- [ ] ✅ 啟用 `pool_pre_ping=True`（避免使用失效連接）
- [ ] ✅ 設置 `pool_recycle`（1-2 小時）
- [ ] ✅ 設置適當的 `pool_timeout`（10-30 秒）
- [ ] ✅ 確保 Session 正確關閉（使用 try-finally）
- [ ] ✅ 添加連接池監控
- [ ] ✅ 計算所有實例的總連接數不超過資料庫限制
- [ ] ✅ 配置資料庫連接超時
- [ ] ✅ 準備連接池耗盡的告警

### 9.3 開發環境建議

```python
# 簡化配置，專注開發
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 顯示 SQL
    pool_size=5,
    max_overflow=5,
)
```

### 9.4 不要做的事情 ❌

```python
# ❌ 不要在請求處理中創建 Engine
@app.get("/users")
def get_users():
    engine = create_engine(DATABASE_URL)  # 錯誤！
    # 每個請求都創建新的連接池

# ❌ 不要手動管理連接
@app.get("/users")
def get_users():
    conn = engine.connect()  # 錯誤！
    # 應該使用 Session

# ❌ 不要忘記關閉 Session
def bad_function():
    session = SessionLocal()
    return session.query(User).all()
    # 忘記 session.close()

# ❌ 不要設置過大的連接池
engine = create_engine(
    DATABASE_URL,
    pool_size=1000,  # 錯誤！太大了
)
```

---

## 十、您的行動計劃

### 立即可做（Priority 1）

1. **更新配置文件**

```python
# infra/db/session.py
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_size=20,  # ← 添加
    max_overflow=10,  # ← 添加
    pool_timeout=30,  # ← 添加
    pool_recycle=3600,  # ← 添加
    pool_pre_ping=True,  # ← 添加
)
```

2. **添加環境變數配置**

```python
# config.py
class Settings(BaseSettings):
    # ... 現有配置 ...
    
    # 連接池配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
```

3. **添加健康檢查端點**

```python
# api/health.py
@router.get("/health/db")
def database_health():
    pool = engine.pool
    return {
        "status": "healthy",
        "pool": {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
        }
    }
```

### 後續優化（Priority 2）

4. **添加監控指標**
5. **壓力測試確定最佳配置**
6. **設置告警（連接池使用率 > 80%）**

---

## 相關文檔

- [性能分析-對象創建與 GC 壓力.md](./性能分析-對象創建與%20GC%20壓力.md)
- [依賴注入流程詳解.md](./依賴注入流程詳解.md)
- [新增功能指南-User CRUD-01-基礎架構.md](./新增功能指南-User%20CRUD-01-基礎架構.md)

## 參考資料

- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [FastAPI Depends](https://fastapi.tiangolo.com/tutorial/dependencies/)

