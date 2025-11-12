"""訂單狀態枚舉"""
from enum import Enum


class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

