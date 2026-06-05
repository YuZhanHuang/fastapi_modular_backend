"""
FastAPI 依賴注入

透過 inject_service 泛型工廠，自動從 wiring 組裝 Service 實例。
"""
from typing import Callable, Type, TypeVar

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infra.db.session import get_session
from app.infra.wiring import get_service

T = TypeVar("T")


def inject_service(service_type: Type[T]) -> Callable[..., T]:
    """
    建立 FastAPI 依賴：依請求注入指定 Service 實例。

    用法（於路由模組）::

        CartServiceDep = Annotated[CartService, Depends(inject_service(CartService))]

        def get_cart(service: CartServiceDep) -> ...:
            ...
    """

    def _dependency(session: Session = Depends(get_session)) -> T:
        return get_service(service_type, session)

    return _dependency
