"""
Wiring 模組

提供自動化的依賴注入與組裝機制。

主要接口：
- get_repository(): 創建 Repository 實例
- get_service(): 創建 Service 實例，自動解析依賴
"""
from app.infra.wiring.factories import get_repository, get_service
from app.infra.wiring.registry import get_registry, DependencyRegistry

__all__ = [
    "get_repository",
    "get_service",
    "get_registry",
    "DependencyRegistry",
]

