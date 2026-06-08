from app.core.exceptions.base import DomainError
from app.core.exceptions.cart import CartNotFoundError, InvalidQuantityError

EXCEPTION_MAPPINGS: dict[type[DomainError], int] = {
    CartNotFoundError: 404,
    InvalidQuantityError: 400,
}
