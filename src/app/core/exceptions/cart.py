from app.core.exceptions.base import DomainError


class InvalidQuantityError(DomainError):
    default_message = "quantity must be positive"
    default_error_code = "INVALID_QUANTITY"


class CartNotFoundError(DomainError):
    default_error_code = "CART_NOT_FOUND"

    def __init__(self, user_id: str) -> None:
        super().__init__(
            message=f"購物車 (user_id: {user_id}) 不存在",
            error_code=self.default_error_code,
        )
