from typing import Callable

from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from app.core.repositories.cart_repository import CartRepository
from app.core.services.cart_service import CartService


def _create_cart_service(
    cart_repository_factory: Callable[..., CartRepository],
    session: Session,
) -> CartService:
    return CartService(cart_repo=cart_repository_factory(session=session))


class ServiceContainer(containers.DeclarativeContainer):
    repos = providers.DependenciesContainer()

    cart_service = providers.Factory(
        _create_cart_service,
        cart_repository_factory=repos.cart_repository.provider,
        session=providers.Dependency(instance_of=Session),
    )
