from app.core.exceptions.base import DomainError
from app.core.exceptions.common import EntityNotFoundError, InvalidEntityTypeError

EXCEPTION_MAPPINGS: dict[type[DomainError], int] = {
    EntityNotFoundError: 404,
    InvalidEntityTypeError: 400,
}
