"""訂單聚合根"""
from dataclasses import dataclass, field
from typing import List

from app.core.domain.order.order_item import OrderItem
from app.core.domain.order.order_status import OrderStatus
from app.core.domain.order.shipping_address import ShippingAddress


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
            raise ValueError("quantity must be positive")
        
        if self.status != OrderStatus.PENDING:
            raise ValueError("只能修改待處理的訂單")
        
        # 檢查是否已存在相同項目
        for item in self.items:
            if item.item_id == item_id:
                raise ValueError(f"項目 {item_id} 已存在")
        
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
            raise ValueError("只能確認待處理的訂單")
        
        if not self.items:
            raise ValueError("訂單必須包含至少一個項目")
        
        if not self.shipping_address:
            raise ValueError("訂單必須有配送地址")
        
        self.status = OrderStatus.CONFIRMED

    def cancel(self) -> None:
        """取消訂單"""
        if self.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise ValueError("已送達或已取消的訂單無法取消")
        
        self.status = OrderStatus.CANCELLED

    def total_amount(self) -> int:
        """計算訂單總金額"""
        return sum(item.unit_price * item.quantity for item in self.items)

