"""
泛型工廠

提供統一的工廠函數來創建 Repository 和 Service 實例。
"""
from typing import Type, TypeVar, Generic
from sqlalchemy.orm import Session

from app.infra.wiring.registry import get_registry
from app.infra.wiring.dependency_resolver import DependencyResolver

T = TypeVar('T')


def get_repository(repository_type: Type[T], session: Session) -> T:
    """
    泛型工廠：創建 Repository 實例
    
    :param repository_type: Repository 接口類型
    :param session: SQLAlchemy Session
    :return: Repository 實例
    """
    registry = get_registry()
    impl_class = registry.get_repository_implementation(repository_type)
    
    if impl_class is None:
        raise ValueError(
            f"No implementation found for repository: {repository_type.__name__}. "
            f"Make sure {repository_type.__name__}Impl exists in infra/db/repositories/"
        )
    
    # 創建實例
    resolver = DependencyResolver(session)
    return resolver._create_repository_instance(impl_class)


def get_service(service_type: Type[T], session: Session) -> T:
    """
    泛型工廠：創建 Service 實例，自動解析並注入依賴
    
    :param service_type: Service 類型
    :param session: SQLAlchemy Session
    :return: Service 實例
    """
    resolver = DependencyResolver(session)
    dependencies = resolver.resolve_service_dependencies(service_type)
    
    return service_type(**dependencies)

