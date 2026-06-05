from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from app.infra.db.repositories.cart_repository_impl import CartRepositoryImpl


class RepositoryContainer(containers.DeclarativeContainer):
    infra = providers.DependenciesContainer()

    cart_repository = providers.Factory(
        CartRepositoryImpl,
        session=providers.Dependency(instance_of=Session),
    )
