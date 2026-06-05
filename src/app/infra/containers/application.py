from dependency_injector import containers, providers

from app.infra.containers.infrastructure import InfrastructureContainer
from app.infra.containers.repositories import RepositoryContainer
from app.infra.containers.services import ServiceContainer


class ApplicationContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration()

    config = providers.Configuration()
    infra = providers.Container(InfrastructureContainer, config=config)
    repos = providers.Container(RepositoryContainer, infra=infra)
    services = providers.Container(ServiceContainer, repos=repos)
