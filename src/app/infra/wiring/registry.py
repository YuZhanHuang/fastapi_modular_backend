"""
依賴註冊表

統一管理所有 Repository 接口到實作的映射關係。
"""
from typing import Dict, Type, Optional
from sqlalchemy.orm import Session

from app.infra.wiring.auto_discovery import discover_repositories, discover_services


class DependencyRegistry:
    """依賴註冊表"""
    
    def __init__(self):
        self._repository_map: Dict[Type, Type] = {}
        self._services: list[Type] = []
        self._initialized = False
    
    def initialize(self):
        """初始化註冊表，自動發現所有依賴"""
        if self._initialized:
            return
        
        # 自動發現並註冊
        self._repository_map = discover_repositories()
        self._services = discover_services()
        self._initialized = True
    
    def register_repository(self, interface: Type, implementation: Type):
        """
        手動註冊 Repository 映射
        
        :param interface: Repository 接口類別
        :param implementation: RepositoryImpl 實作類別
        """
        self._repository_map[interface] = implementation
    
    def get_repository_implementation(self, interface: Type) -> Optional[Type]:
        """
        獲取 Repository 接口對應的實作類別
        
        :param interface: Repository 接口類別
        :return: RepositoryImpl 實作類別，如果不存在則返回 None
        """
        if not self._initialized:
            self.initialize()
        
        return self._repository_map.get(interface)
    
    def get_all_services(self) -> list[Type]:
        """獲取所有 Service 類別"""
        if not self._initialized:
            self.initialize()
        
        return self._services.copy()
    
    def is_registered(self, interface: Type) -> bool:
        """檢查 Repository 接口是否已註冊"""
        if not self._initialized:
            self.initialize()
        
        return interface in self._repository_map


# 全局註冊表實例
_registry = DependencyRegistry()


def get_registry() -> DependencyRegistry:
    """獲取全局註冊表實例"""
    return _registry

