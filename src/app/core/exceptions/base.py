from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class DomainErrorDetail:
    message: str
    field: str | None = None
    code: str | None = None


class DomainError(Exception):
    default_message: ClassVar[str] = "業務規則錯誤"
    default_error_code: ClassVar[str] = "DOMAIN_ERROR"

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        errors: list[DomainErrorDetail] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.error_code = error_code or self.default_error_code
        self.errors = errors
        super().__init__(self.message)
