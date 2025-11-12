"""配送地址值對象"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ShippingAddress:
    """配送地址（值對象）"""
    street: str
    city: str
    postal_code: str
    country: str

