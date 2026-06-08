"""Auto-discover DomainError HTTP mappings and register unified exception handlers."""

from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
import traceback
from typing import TYPE_CHECKING

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.utils.response import (
    domain_error_to_response,
    error_response_to_json,
    unhandled_exception_to_response,
    validation_error_from_pydantic,
)
from app.core.exceptions.base import DomainError

if TYPE_CHECKING:
    from fastapi import FastAPI

EXCEPTIONS_PACKAGE = "app.api.exceptions"
CORE_EXCEPTIONS_PACKAGE = "app.core.exceptions"


def discover_mappings() -> dict[type[DomainError], int]:
    """Import mapping modules under EXCEPTIONS_PACKAGE and merge EXCEPTION_MAPPINGS."""
    package = importlib.import_module(EXCEPTIONS_PACKAGE)
    mappings: dict[type[DomainError], int] = {}
    registered_names: list[str] = []

    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{EXCEPTIONS_PACKAGE}.{module_info.name}")
        module_mappings = getattr(module, "EXCEPTION_MAPPINGS", None)
        if module_mappings is None:
            continue
        if not isinstance(module_mappings, dict):
            raise RuntimeError(
                f"{EXCEPTIONS_PACKAGE}.{module_info.name}.EXCEPTION_MAPPINGS must be a dict"
            )

        for exc_type, status_code in module_mappings.items():
            if exc_type in mappings:
                raise RuntimeError(
                    f"Duplicate HTTP mapping for {exc_type.__name__}: "
                    f"{mappings[exc_type]} and {status_code}"
                )
            mappings[exc_type] = status_code

        registered_names.append(module_info.name)

    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    if is_debug:
        for name in registered_names:
            print(f"[exception_handlers] registered mappings: {name}")

    return mappings


def discover_domain_error_types() -> list[type[DomainError]]:
    """Scan core/exceptions/ for concrete DomainError subclasses."""
    package = importlib.import_module(CORE_EXCEPTIONS_PACKAGE)
    types: list[type[DomainError]] = []

    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if module_info.name.startswith("_") or module_info.name == "base":
            continue

        module = importlib.import_module(f"{CORE_EXCEPTIONS_PACKAGE}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, DomainError)
                and obj is not DomainError
                and obj.__module__ == module.__name__
            ):
                types.append(obj)

    return types


def validate_mappings(
    mappings: dict[type[DomainError], int],
    types: list[type[DomainError]],
) -> None:
    """Fail fast when a DomainError subclass lacks an HTTP mapping."""
    missing = [exc_type for exc_type in types if exc_type not in mappings]
    if missing:
        names = ", ".join(exc_type.__name__ for exc_type in sorted(missing, key=lambda t: t.__name__))
        raise RuntimeError(f"Missing HTTP mappings for DomainError subclasses: {names}")


async def handle_request_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    body = validation_error_from_pydantic(
        exc, "輸入驗證失敗", skip_request_prefix=True
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response_to_json(body),
    )


async def handle_pydantic_validation_error(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    body = validation_error_from_pydantic(
        exc, "數據驗證失敗", skip_request_prefix=False
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response_to_json(body),
    )


async def handle_unhandled_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    error_resp = unhandled_exception_to_response(exc)
    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    print(f"[ERROR] Unhandled exception: {exc}")
    if is_debug:
        traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response_to_json(error_resp),
    )


async def handle_domain_error(
    request: Request,
    exc: DomainError,
    status_code: int,
) -> JSONResponse:
    body = domain_error_to_response(exc, status_code)
    return JSONResponse(
        status_code=status_code,
        content=error_response_to_json(body),
    )


def _register_domain_error_handlers(app: FastAPI) -> None:
    mappings = discover_mappings()
    types = discover_domain_error_types()
    validate_mappings(mappings, types)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return await handle_domain_error(request, exc, mappings[type(exc)])


def _register_builtin_handlers(app: FastAPI) -> None:
    app.exception_handler(RequestValidationError)(handle_request_validation_error)
    app.exception_handler(ValidationError)(handle_pydantic_validation_error)
    app.exception_handler(Exception)(handle_unhandled_exception)


def register_exception_handlers(app: FastAPI) -> None:
    _register_domain_error_handlers(app)
    _register_builtin_handlers(app)
