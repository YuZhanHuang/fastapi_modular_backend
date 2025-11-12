"""
Domain 層模組

導出所有聚合根和主要實體，方便其他層使用。
"""

from app.core.domain.cart import Cart, CartItem

__all__ = [
    "Cart",
    "CartItem",
]

