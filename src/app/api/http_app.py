"""
HTTP 介面層

只負責 FastAPI 應用程式的 HTTP 相關配置：
- FastAPI 應用實例創建
- 路由註冊
- Middleware 配置
- CORS 配置
- 全局異常處理
等 HTTP 層面的設定

不包含：
- 資料庫初始化（應在應用層處理）
- 業務邏輯（應在服務層處理）
"""
from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.router_discovery import register_routers


def create_http_app() -> FastAPI:
    """
    創建 FastAPI HTTP 應用程式
    
    只負責 HTTP 層面的配置，包括：
    - 路由註冊
    - 全局異常處理器
    - 中間件配置
    
    :return: FastAPI 應用實例
    """
    app = FastAPI(
        title="Cart Service",
        version="1.0.0",
        description="基於 Clean Architecture 的購物車服務",
    )

    register_exception_handlers(app)
    register_routers(app)

    return app
