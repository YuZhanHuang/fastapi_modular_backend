"""Auto-discover and register API routers from app.api.routers."""

from __future__ import annotations

import importlib
import os
import pkgutil
from typing import TYPE_CHECKING

from fastapi import APIRouter

if TYPE_CHECKING:
    from fastapi import FastAPI

DEFAULT_API_PREFIX = "/api"
ROUTERS_PACKAGE = "app.api.routers"


def discover_routers() -> list[APIRouter]:
    """Import router modules under ROUTERS_PACKAGE and collect APIRouter instances."""
    package = importlib.import_module(ROUTERS_PACKAGE)
    routers: list[APIRouter] = []
    registered_names: list[str] = []

    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{ROUTERS_PACKAGE}.{module_info.name}")
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            routers.append(router)
            registered_names.append(module_info.name)

    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    if is_debug:
        for name in registered_names:
            print(f"[router_discovery] registered: {name}")

    return routers


def register_routers(app: FastAPI, *, prefix: str = DEFAULT_API_PREFIX) -> None:
    """Register all discovered routers on the FastAPI application."""
    for router in discover_routers():
        app.include_router(router, prefix=prefix)
