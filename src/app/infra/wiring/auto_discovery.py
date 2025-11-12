"""
自動發現機制

基於命名約定自動掃描和發現所有 Repository 和 Service 類別。
"""
import importlib
import inspect
from typing import Dict, Type, List
from pathlib import Path


def discover_repositories() -> Dict[Type, Type]:
    """
    自動發現所有 Repository 接口和對應的實作類別
    
    命名約定：
    - 接口：core/repositories/{entity}_repository.py -> {Entity}Repository
    - 實作：infra/db/repositories/{entity}_repository_impl.py -> {Entity}RepositoryImpl
    
    :return: 字典，key 為 Repository 接口，value 為 RepositoryImpl 實作
    """
    repository_map: Dict[Type, Type] = {}
    
    # 掃描 core/repositories/ 目錄
    core_repos_path = Path(__file__).parent.parent.parent / "core" / "repositories"
    infra_repos_path = Path(__file__).parent.parent / "db" / "repositories"
    
    # 獲取所有 Repository 接口
    repo_interfaces = _scan_repository_interfaces(core_repos_path)
    
    # 獲取所有 RepositoryImpl 實作
    repo_implementations = _scan_repository_implementations(infra_repos_path)
    
    # 建立映射關係（基於命名約定）
    for interface_name, interface_class in repo_interfaces.items():
        impl_name = interface_name.replace("Repository", "RepositoryImpl")
        if impl_name in repo_implementations:
            repository_map[interface_class] = repo_implementations[impl_name]
    
    return repository_map


def discover_services() -> List[Type]:
    """
    自動發現所有 Service 類別
    
    :return: Service 類別列表
    """
    services_path = Path(__file__).parent.parent.parent / "core" / "services"
    return _scan_service_classes(services_path)


def _scan_repository_interfaces(repos_path: Path) -> Dict[str, Type]:
    """掃描 Repository 接口"""
    interfaces: Dict[str, Type] = {}
    
    if not repos_path.exists():
        return interfaces
    
    # 動態導入模組
    for module_file in repos_path.glob("*_repository.py"):
        module_name = module_file.stem
        full_module_name = f"app.core.repositories.{module_name}"
        
        try:
            module = importlib.import_module(full_module_name)
            # 查找 Repository 類別（繼承 ABC 的類別）
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (name.endswith("Repository") and 
                    name != "Repository" and
                    inspect.isabstract(obj)):
                    interfaces[name] = obj
        except Exception as e:
            # 忽略導入錯誤，繼續掃描
            continue
    
    return interfaces


def _scan_repository_implementations(repos_path: Path) -> Dict[str, Type]:
    """掃描 RepositoryImpl 實作"""
    implementations: Dict[str, Type] = {}
    
    if not repos_path.exists():
        return implementations
    
    # 動態導入模組
    for module_file in repos_path.glob("*_repository_impl.py"):
        module_name = module_file.stem
        full_module_name = f"app.infra.db.repositories.{module_name}"
        
        try:
            module = importlib.import_module(full_module_name)
            # 查找 RepositoryImpl 類別
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (name.endswith("RepositoryImpl") and 
                    not inspect.isabstract(obj)):
                    implementations[name] = obj
        except Exception as e:
            # 忽略導入錯誤，繼續掃描
            continue
    
    return implementations


def _scan_service_classes(services_path: Path) -> List[Type]:
    """掃描 Service 類別"""
    services: List[Type] = []
    
    if not services_path.exists():
        return services
    
    # 動態導入模組
    for module_file in services_path.glob("*_service.py"):
        module_name = module_file.stem
        full_module_name = f"app.core.services.{module_name}"
        
        try:
            module = importlib.import_module(full_module_name)
            # 查找 Service 類別
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (name.endswith("Service") and 
                    not inspect.isabstract(obj) and
                    name != "Service"):
                    services.append(obj)
        except Exception as e:
            # 忽略導入錯誤，繼續掃描
            continue
    
    return services

