"""
HTTP 介面層

只負責 FastAPI 應用程式的 HTTP 相關配置：
- FastAPI 應用實例創建
- 路由註冊
- Middleware 配置
- CORS 配置
等 HTTP 層面的設定

不包含：
- 資料庫初始化（應在應用層處理）
- 業務邏輯（應在服務層處理）
"""
from fastapi import FastAPI

from app.api import carts


def create_http_app() -> FastAPI:
    """
    創建 FastAPI HTTP 應用程式
    
    只負責 HTTP 層面的配置，不包含基礎設施初始化
    
    :return: FastAPI 應用實例
    """
    app = FastAPI(
        title="Cart Service",
        version="1.0.0",
    )

    app.include_router(carts.router, prefix="/api")

    return app

