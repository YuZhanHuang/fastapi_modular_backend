from __future__ import annotations

from typing import Any

from app.core.exceptions.base import DomainError


class InvalidEntityTypeError(DomainError):
    default_error_code = "INVALID_ENTITY_TYPE"

    def __init__(self, model: Any, expected_type: type) -> None:
        super().__init__(
            message=f"{model} is not of type {expected_type}",
            error_code=self.default_error_code,
        )


class EntityNotFoundError(DomainError):
    default_error_code = "ENTITY_NOT_FOUND"

    def __init__(
        self,
        entity_name: str,
        *,
        entity_id: Any = None,
        conditions: dict[str, Any] | None = None,
    ) -> None:
        if entity_id is not None:
            message = f"{entity_name} with id {entity_id} not found"
        elif conditions:
            message = f"{entity_name} not found with conditions: {conditions}"
        else:
            message = f"{entity_name} not found"

        super().__init__(message=message, error_code=self.default_error_code)
