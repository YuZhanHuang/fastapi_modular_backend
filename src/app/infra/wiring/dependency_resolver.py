"""
依賴解析器

自動解析 Service 的 __init__ 簽名，識別需要的依賴並自動注入。
"""
import inspect
from typing import Dict, Type, Any, get_type_hints, get_origin, get_args
from sqlalchemy.orm import Session

from app.infra.wiring.registry import get_registry


class DependencyResolver:
    """依賴解析器"""
    
    def __init__(self, session: Session):
        self.session = session
        self._cache: Dict[Type, Any] = {}  # 依賴實例快取
    
    def resolve_service_dependencies(self, service_class: Type) -> Dict[str, Any]:
        """
        解析 Service 類別的所有依賴
        
        :param service_class: Service 類別
        :return: 依賴字典，key 為參數名，value 為依賴實例
        """
        dependencies = {}
        
        # 獲取 __init__ 方法的簽名
        init_signature = inspect.signature(service_class.__init__)
        
        # 跳過 self 參數
        for param_name, param in list(init_signature.parameters.items())[1:]:
            # 獲取參數類型
            param_type = param.annotation
            
            if param_type == inspect.Parameter.empty:
                continue
            
            # 解析依賴
            dependency_instance = self._resolve_dependency(param_type)
            if dependency_instance is not None:
                dependencies[param_name] = dependency_instance
        
        return dependencies
    
    def _resolve_dependency(self, dependency_type: Type) -> Any:
        """
        解析單個依賴
        
        :param dependency_type: 依賴類型
        :return: 依賴實例
        """
        # 檢查快取
        if dependency_type in self._cache:
            return self._cache[dependency_type]
        
        # 處理 Session 類型
        if dependency_type == Session:
            return self.session
        
        # 處理 Repository 類型
        registry = get_registry()
        impl_class = registry.get_repository_implementation(dependency_type)
        
        if impl_class:
            # 創建 Repository 實例
            instance = self._create_repository_instance(impl_class)
            self._cache[dependency_type] = instance
            return instance
        
        # 處理 Port 類型（未來擴展）
        # TODO: 實現 Port 的解析
        
        return None
    
    def _create_repository_instance(self, impl_class: Type) -> Any:
        """
        創建 Repository 實例
        
        :param impl_class: RepositoryImpl 類別
        :return: Repository 實例
        """
        # 檢查 __init__ 簽名，確定需要的參數
        init_signature = inspect.signature(impl_class.__init__)
        params = {}
        
        for param_name, param in list(init_signature.parameters.items())[1:]:
            param_type = param.annotation
            
            if param_type == Session:
                params[param_name] = self.session
            elif param_type != inspect.Parameter.empty:
                # 遞迴解析其他依賴
                dependency = self._resolve_dependency(param_type)
                if dependency is not None:
                    params[param_name] = dependency
        
        return impl_class(**params)

