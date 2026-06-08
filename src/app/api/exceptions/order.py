from app.core.exceptions.base import DomainError
from app.core.exceptions.order import (
    DuplicateOrderItemError,
    EmptyOrderError,
    InvalidOrderQuantityError,
    InvalidOrderStateError,
    MissingShippingAddressError,
)

EXCEPTION_MAPPINGS: dict[type[DomainError], int] = {
    InvalidOrderQuantityError: 400,
    InvalidOrderStateError: 400,
    DuplicateOrderItemError: 409,
    EmptyOrderError: 400,
    MissingShippingAddressError: 400,
}
