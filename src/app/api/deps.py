"""
FastAPI 依賴注入

透過 inject_service 橋接 dependency-injector Factory，組裝 Service 實例。
"""
from typing import Callable, TypeVar

from dependency_injector import providers
from fastapi import Depends
from sqlalchemy.orm import Session

from app.infra.db.session import get_session

T = TypeVar("T")


def inject_service(provider: providers.Factory[T]) -> Callable[..., T]:
    """
    建立 FastAPI 依賴：依請求注入指定 Service 實例。

    用法（於路由模組）::

        CartServiceDep = Annotated[
            CartService,
            Depends(inject_service(get_container().services.cart_service)),
        ]

        def get_cart(service: CartServiceDep) -> ...:
            ...
    """

    def _dependency(session: Session = Depends(get_session)) -> T:
        return provider(session=session)

    return _dependency
