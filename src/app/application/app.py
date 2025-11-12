"""
應用程式初始化入口

負責：
1. 初始化基礎設施（資料庫、Redis 等）
2. 組裝應用程式組件
3. 創建並配置 FastAPI 應用實例
"""
import os
from typing import Optional

from fastapi import FastAPI

from app.api.factory import APIAppFactory
from app.config import settings
from app.infra.db.base import Base
from app.infra.db.session import engine


def init_database(create_tables: bool = False) -> None:
    """
    初始化資料庫
    
    :param create_tables: 是否創建資料表（僅開發環境使用）
                         生產環境應使用 Alembic migrations
    """
    if create_tables:
        # 僅在開發環境使用，生產環境應使用 Alembic migrations
        Base.metadata.create_all(bind=engine)


def create_app(
    init_db: Optional[bool] = None,
    create_tables: bool = False,
    api_type: Optional[str] = None,
) -> FastAPI:
    """
    創建並初始化應用程式
    
    :param init_db: 是否初始化資料庫（None 時根據環境變數決定）
    :param create_tables: 是否創建資料表（僅開發環境）
    :param api_type: API 類型（如 "http", "graphql"），如果為 None 則從環境變數讀取
    :return: FastAPI 應用實例
    """

    if init_db is None:
        is_production = os.getenv("ENVIRONMENT", "").lower() == "production"
        run_migrations = os.getenv("RUN_MIGRATIONS", "1") == "1"
        init_db = not is_production and not run_migrations
    
    if init_db:
        init_database(create_tables=create_tables)
    
    # 使用工廠創建 API 應用
    app = APIAppFactory.create(api_type)
    
    return app


app = create_app(
    init_db=False,
    create_tables=False,
)

