"""
API 應用工廠

統一管理所有 API 類型的創建邏輯，支援動態註冊和擴展。

使用工廠模式解決多 API 創建問題：
- 符合依賴倒置原則：application 層只依賴抽象
- 符合開放封閉原則：新增 API 類型只需註冊，無需修改 application/app.py
- 職責清晰：工廠負責管理 API 創建，application 層只負責組裝
"""
import os
from typing import Dict, Callable, Optional
from fastapi import FastAPI


class APIAppFactory:
    """
    API 應用工廠
    
    統一管理所有 API 類型的創建邏輯，支援動態註冊和擴展。
    """
    
    _factories: Dict[str, Callable[[], FastAPI]] = {}
    
    @classmethod
    def register(cls, api_type: str, factory: Callable[[], FastAPI]) -> None:
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
        """
        獲取所有已註冊的 API 類型
        
        :return: API 類型列表
        """
        return list(cls._factories.keys())
    
    @classmethod
    def is_registered(cls, api_type: str) -> bool:
        """
        檢查 API 類型是否已註冊
        
        :param api_type: API 類型名稱
        :return: 是否已註冊
        """
        return api_type in cls._factories


# 註冊 HTTP API（預設）
from app.api.http_app import create_http_app
APIAppFactory.register("http", create_http_app)

# 未來註冊其他 API 時，只需在這裡添加：
# from app.api.graphql_app import create_graphql_app
# APIAppFactory.register("graphql", create_graphql_app)
#
# from app.api.websocket_app import create_websocket_app
# APIAppFactory.register("websocket", create_websocket_app)

