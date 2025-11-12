"""訂單項目實體"""
from dataclasses import dataclass


@dataclass
class OrderItem:
    """訂單項目（實體）"""
    item_id: str
    product_id: str
    quantity: int
    unit_price: int  # in smallest currency unit, e.g. cents

