from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from fastapi.testclient import TestClient
from httpx import Response

from app.core.services.cart_service import CartService
from app.infra.containers.application import ApplicationContainer


@dataclass
class ScenarioContext:
    """Share state between Gherkin Given/When/Then steps within a scenario."""

    service: Optional[CartService] = None
    repo: Any = None
    result: Any = None
    exception: Optional[BaseException] = None
    client: Optional[TestClient] = None
    container: Optional[ApplicationContainer] = None
    response: Optional[Response] = None
    _cleanups: list[tuple[Callable[..., None], tuple, dict]] = field(
        default_factory=list
    )

    def add_cleanup(self, fn: Callable[..., None], *args: Any, **kwargs: Any) -> None:
        self._cleanups.append((fn, args, kwargs))

    def run_cleanups(self) -> None:
        for fn, args, kwargs in reversed(self._cleanups):
            fn(*args, **kwargs)
        self._cleanups.clear()
