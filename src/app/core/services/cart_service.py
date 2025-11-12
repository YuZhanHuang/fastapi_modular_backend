from typing import Optional

from app.core.domain.cart import Cart
from app.core.repositories.cart_repository import CartRepository


class CartService:
    def __init__(self, cart_repo: CartRepository):
        self.cart_repo = cart_repo

    def get_cart(self, user_id: str) -> Cart:
        cart: Optional[Cart] = self.cart_repo.get_by_user_id(user_id)
        return cart or Cart(user_id=user_id)

    def add_item(self, user_id: str, product_id: str, unit_price: int, quantity: int = 1) -> Cart:
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        cart = self.cart_repo.get_by_user_id(user_id) or Cart(user_id=user_id)
        cart.add_item(product_id=product_id, unit_price=unit_price, quantity=quantity)
        self.cart_repo.save(cart)
        return cart


