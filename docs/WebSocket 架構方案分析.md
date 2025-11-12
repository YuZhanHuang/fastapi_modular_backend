# WebSocket 架構方案分析

## 問題

如果需要 WebSocket 作為即時通知，是否需要另外起一個 process 專門處理 WebSocket 的請求？

---

## 答案：視情況而定

**簡短回答：**
- **小規模應用**：可以與 HTTP API 共用同一個 process ✅
- **大規模應用**：建議使用單獨的 process ⭐
- **最佳方案**：支援兩種模式，根據需求選擇 🔥

---

## 方案比較

### 方案 A：同一個 Process（HTTP + WebSocket）

**架構：**
```
┌─────────────────────────────────┐
│  uvicorn (Process 1)            │
│  ├── HTTP API                   │
│  └── WebSocket                  │
└─────────────────────────────────┘
```

**實作方式：**

```python
# api/websocket_app.py
from fastapi import FastAPI, WebSocket
from app.api import carts  # HTTP 路由

def create_websocket_app() -> FastAPI:
    app = FastAPI()
    
    # HTTP 路由
    app.include_router(carts.router, prefix="/api")
    
    # WebSocket 路由
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        # WebSocket 邏輯
        ...
    
    return app
```

**優點：**
- ✅ **簡單**：只需一個 process，部署簡單
- ✅ **資源節省**：不需要額外的 process
- ✅ **共享狀態**：HTTP 和 WebSocket 可以共享記憶體狀態
- ✅ **適合小規模**：連接數少時性能足夠

**缺點：**
- ❌ **資源競爭**：HTTP 請求可能影響 WebSocket 性能
- ❌ **擴展困難**：無法獨立擴展 HTTP 和 WebSocket
- ❌ **單點故障**：一個服務掛掉，兩個都受影響
- ❌ **記憶體壓力**：大量 WebSocket 連接會佔用記憶體

**適用場景：**
- 小規模應用（< 1000 並發連接）
- 開發環境
- 原型開發

---

### 方案 B：單獨的 Process（推薦）⭐

**架構：**
```
┌─────────────────────┐     ┌─────────────────────┐
│  uvicorn (HTTP)     │     │  uvicorn (WebSocket) │
│  Process 1          │     │  Process 2          │
│  └── HTTP API       │     │  └── WebSocket      │
└─────────────────────┘     └─────────────────────┘
         │                            │
         └──────────┬─────────────────┘
                    │
            ┌───────▼────────┐
            │   Redis/DB      │
            │   (共享狀態)    │
            └────────────────┘
```

**實作方式：**

**1. 創建 WebSocket App**

```python
# api/websocket_app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, Set

class ConnectionManager:
    """管理 WebSocket 連接"""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)
    
    async def broadcast(self, message: str):
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                await connection.send_text(message)

manager = ConnectionManager()

def create_websocket_app() -> FastAPI:
    app = FastAPI(title="WebSocket Service")
    
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        await manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_text()
                # 處理 WebSocket 訊息
                await manager.send_personal_message(f"Echo: {data}", user_id)
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
    
    return app
```

**2. 註冊到工廠**

```python
# api/factory.py
from app.api.websocket_app import create_websocket_app
APIAppFactory.register("websocket", create_websocket_app)
```

**3. 更新 entrypoint.sh**

```bash
# docker/app/entrypoint.sh
case "${SERVICE_ROLE:-api}" in
  api)
    echo "[entrypoint] Starting HTTP API..."
    exec uv run uvicorn app.application.app:app --host 0.0.0.0 --port 8000
    ;;
  websocket)
    echo "[entrypoint] Starting WebSocket service..."
    exec uv run uvicorn app.application.app:app --host 0.0.0.0 --port 8001 \
      --env-file <(echo "API_TYPE=websocket")
    ;;
  # ...
esac
```

**4. 更新 docker-compose.yml**

```yaml
services:
  app:
    environment:
      SERVICE_ROLE: api
      API_TYPE: http
    ports:
      - "8000:8000"
  
  websocket:
    build:
      context: .
      dockerfile: docker/app/Dockerfile
    environment:
      SERVICE_ROLE: websocket
      API_TYPE: websocket
      DB_HOST: db
      DB_PORT: 5432
      DATABASE_URL: postgresql+psycopg://app:app@db:5432/app
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - db
      - redis
    ports:
      - "8001:8001"
```

**優點：**
- ✅ **獨立擴展**：可以獨立擴展 HTTP 和 WebSocket
- ✅ **資源隔離**：HTTP 請求不會影響 WebSocket 性能
- ✅ **故障隔離**：一個服務掛掉不影響另一個
- ✅ **專業化**：可以針對 WebSocket 優化配置
- ✅ **適合大規模**：支援大量並發連接

**缺點：**
- ⚠️ **複雜度增加**：需要管理兩個 process
- ⚠️ **資源消耗**：需要額外的 process 和記憶體
- ⚠️ **狀態共享**：需要透過 Redis/DB 共享狀態

**適用場景：**
- 大規模應用（> 1000 並發連接）
- 生產環境
- 需要獨立擴展的場景

---

### 方案 C：混合方案（最靈活）🔥

**架構：**
```
支援兩種模式：
1. 單一 process（開發/小規模）
2. 分離 process（生產/大規模）
```

**實作方式：**

通過環境變數控制：

```bash
# 模式 1：單一 process（HTTP + WebSocket）
SERVICE_ROLE=api
API_TYPE=combined  # 新增 combined 類型

# 模式 2：分離 process
SERVICE_ROLE=api      # HTTP
API_TYPE=http

SERVICE_ROLE=websocket  # WebSocket
API_TYPE=websocket
```

**創建 Combined App：**

```python
# api/combined_app.py
from fastapi import FastAPI
from app.api.http_app import create_http_app
from app.api.websocket_app import create_websocket_app

def create_combined_app() -> FastAPI:
    """結合 HTTP 和 WebSocket 的應用"""
    # 創建 HTTP app
    http_app = create_http_app()
    
    # 添加 WebSocket 路由
    from app.api.websocket_app import manager
    
    @http_app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        await manager.connect(websocket, user_id)
        # ...
    
    return http_app
```

**註冊：**

```python
# api/factory.py
from app.api.combined_app import create_combined_app
APIAppFactory.register("combined", create_combined_app)
```

**優點：**
- ✅ **靈活性高**：可以根據需求選擇模式
- ✅ **開發友好**：開發時使用 combined，生產時分離
- ✅ **漸進式擴展**：從小規模開始，需要時再分離

**缺點：**
- ⚠️ **實作複雜度**：需要維護兩種模式

---

## 狀態共享問題

### 問題

當 HTTP 和 WebSocket 分離時，如何共享狀態？

**場景：**
- HTTP API 收到訂單創建請求
- 需要透過 WebSocket 通知用戶

### 解決方案

#### 方案 1：使用 Redis Pub/Sub（推薦）⭐

**架構：**
```
HTTP API → Redis Pub → WebSocket Service → 用戶
```

**實作：**

```python
# infra/websocket/redis_pubsub.py
import redis
import json
from typing import Callable

class RedisPubSub:
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
    
    def publish_notification(self, user_id: str, message: dict):
        """發布通知"""
        channel = f"notifications:{user_id}"
        self.redis_client.publish(channel, json.dumps(message))
    
    def subscribe_notifications(self, user_id: str, callback: Callable):
        """訂閱通知"""
        channel = f"notifications:{user_id}"
        self.pubsub.subscribe(channel)
        
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                callback(data)
```

**HTTP API 端：**

```python
# api/carts.py
from app.infra.websocket.redis_pubsub import RedisPubSub

@router.post("/cart/items")
def add_item(...):
    cart = service.add_item(...)
    
    # 發布通知
    pubsub = RedisPubSub(settings.REDIS_URL)
    pubsub.publish_notification(
        user_id=user_id,
        message={"type": "cart_updated", "cart": cart}
    )
    
    return cart_out_from_domain(cart)
```

**WebSocket 端：**

```python
# api/websocket_app.py
import asyncio
from app.infra.websocket.redis_pubsub import RedisPubSub

async def listen_notifications(user_id: str, websocket: WebSocket):
    """監聽 Redis 通知並發送給 WebSocket"""
    pubsub = RedisPubSub(settings.REDIS_URL)
    
    def on_message(message):
        asyncio.create_task(websocket.send_json(message))
    
    pubsub.subscribe_notifications(user_id, on_message)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    # 啟動通知監聽
    asyncio.create_task(listen_notifications(user_id, websocket))
    
    try:
        while True:
            data = await websocket.receive_text()
            # 處理訊息
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

#### 方案 2：使用資料庫輪詢（不推薦）

**問題：**
- 延遲高
- 資料庫壓力大
- 不適合即時通知

#### 方案 3：使用 Message Queue（大規模）

**適用場景：**
- 超大規模應用
- 需要保證訊息順序
- 需要持久化

**工具：**
- RabbitMQ
- Apache Kafka
- AWS SQS

---

## 推薦方案

### 階段一：開發/小規模

**使用方案 A（同一個 Process）**

```yaml
# docker-compose.yml
services:
  app:
    environment:
      SERVICE_ROLE: api
      API_TYPE: combined  # HTTP + WebSocket
    ports:
      - "8000:8000"
```

**優點：**
- 簡單快速
- 適合開發和測試
- 資源節省

### 階段二：生產/大規模

**使用方案 B（分離 Process）**

```yaml
# docker-compose.yml
services:
  app:
    environment:
      SERVICE_ROLE: api
      API_TYPE: http
    ports:
      - "8000:8000"
  
  websocket:
    environment:
      SERVICE_ROLE: websocket
      API_TYPE: websocket
    ports:
      - "8001:8001"
```

**狀態共享：**
- 使用 Redis Pub/Sub
- HTTP API 發布通知
- WebSocket Service 訂閱並推送

**優點：**
- 獨立擴展
- 性能優化
- 故障隔離

---

## 實作步驟

### 步驟 1：創建 WebSocket App

```python
# api/websocket_app.py
# （參考上面的範例）
```

### 步驟 2：註冊到工廠

```python
# api/factory.py
from app.api.websocket_app import create_websocket_app
APIAppFactory.register("websocket", create_websocket_app)
```

### 步驟 3：更新 entrypoint.sh

```bash
# 添加 websocket case
websocket)
  echo "[entrypoint] Starting WebSocket service..."
  exec uv run uvicorn app.application.app:app --host 0.0.0.0 --port 8001
  ;;
```

### 步驟 4：更新 docker-compose.yml

```yaml
websocket:
  # （參考上面的範例）
```

### 步驟 5：實作狀態共享（如需要）

```python
# 使用 Redis Pub/Sub
# （參考上面的範例）
```

---

## 總結

### 是否需要單獨的 Process？

**答案：視規模而定**

| 規模 | 並發連接 | 推薦方案 |
|------|---------|---------|
| **小規模** | < 1000 | 同一個 Process ✅ |
| **中規模** | 1000-10000 | 分離 Process ⭐ |
| **大規模** | > 10000 | 分離 Process + Message Queue 🔥 |

### 最佳實踐

1. **開發階段**：使用同一個 Process（簡單）
2. **生產階段**：使用分離 Process（性能）
3. **狀態共享**：使用 Redis Pub/Sub
4. **監控**：分別監控 HTTP 和 WebSocket 的指標

### 你的架構優勢

你的專案已經有：
- ✅ `SERVICE_ROLE` 機制（支援多種角色）
- ✅ `APIAppFactory`（支援多種 API 類型）
- ✅ Redis（可以用於狀態共享）

**因此，實作 WebSocket 分離非常簡單！** 🎉

