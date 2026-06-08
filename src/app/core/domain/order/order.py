"""訂單聚合根"""
from dataclasses import dataclass, field
from typing import List

from app.core.domain.order.order_item import OrderItem
from app.core.domain.order.order_status import OrderStatus
from app.core.domain.order.shipping_address import ShippingAddress
from app.core.exceptions.order import (
    DuplicateOrderItemError,
    EmptyOrderError,
    InvalidOrderQuantityError,
    InvalidOrderStateError,
    MissingShippingAddressError,
)


@dataclass
class Order:
    """訂單（聚合根）"""
    order_id: str
    user_id: str
    items: List[OrderItem] = field(default_factory=list)
    shipping_address: ShippingAddress | None = None
    status: OrderStatus = OrderStatus.PENDING

    def add_item(self, item_id: str, product_id: str, quantity: int, unit_price: int) -> None:
        """添加項目到訂單"""
        if quantity <= 0:
            raise InvalidOrderQuantityError()

        if self.status != OrderStatus.PENDING:
            raise InvalidOrderStateError("只能修改待處理的訂單")

        for item in self.items:
            if item.item_id == item_id:
                raise DuplicateOrderItemError(item_id)
        
        self.items.append(
            OrderItem(
                item_id=item_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price
            )
        )

    def confirm(self) -> None:
        """確認訂單"""
        if self.status != OrderStatus.PENDING:
            raise InvalidOrderStateError("只能確認待處理的訂單")

        if not self.items:
            raise EmptyOrderError()

        if not self.shipping_address:
            raise MissingShippingAddressError()
        
        self.status = OrderStatus.CONFIRMED

    def cancel(self) -> None:
        """取消訂單"""
        if self.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise InvalidOrderStateError("已送達或已取消的訂單無法取消")
        
        self.status = OrderStatus.CANCELLED

    def total_amount(self) -> int:
        """計算訂單總金額"""
        return sum(item.unit_price * item.quantity for item in self.items)

