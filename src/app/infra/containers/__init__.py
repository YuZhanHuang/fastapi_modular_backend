from typing import Optional

from app.config import settings
from app.infra.containers.application import ApplicationContainer

_container: Optional[ApplicationContainer] = None


def _build_config() -> dict[str, str]:
    return {
        "database_url": settings.DATABASE_URL,
        "redis_url": f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    }


def init_container(container: Optional[ApplicationContainer] = None) -> ApplicationContainer:
    """Initialize or replace the global application container."""
    global _container

    if container is not None:
        _container = container
        return _container

    if _container is None:
        _container = ApplicationContainer()
        _container.config.from_dict(_build_config())
        _container.init_resources()

    return _container


def get_container() -> ApplicationContainer:
    """Return the global application container, initializing it if needed."""
    return init_container()


def shutdown_container() -> None:
    """Shut down container resources and clear the global instance."""
    global _container

    if _container is not None:
        _container.shutdown_resources()
        _container = None
