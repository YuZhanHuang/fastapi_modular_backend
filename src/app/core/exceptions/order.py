from app.core.exceptions.base import DomainError


class InvalidOrderQuantityError(DomainError):
    default_message = "quantity must be positive"
    default_error_code = "INVALID_ORDER_QUANTITY"


class InvalidOrderStateError(DomainError):
    default_error_code = "INVALID_ORDER_STATE"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message=message or "訂單狀態不允許此操作",
            error_code=self.default_error_code,
        )


class DuplicateOrderItemError(DomainError):
    default_error_code = "DUPLICATE_ORDER_ITEM"

    def __init__(self, item_id: str) -> None:
        super().__init__(
            message=f"項目 {item_id} 已存在",
            error_code=self.default_error_code,
        )


class EmptyOrderError(DomainError):
    default_message = "訂單必須包含至少一個項目"
    default_error_code = "EMPTY_ORDER"


class MissingShippingAddressError(DomainError):
    default_message = "訂單必須有配送地址"
    default_error_code = "MISSING_SHIPPING_ADDRESS"
