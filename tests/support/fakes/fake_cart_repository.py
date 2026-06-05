from typing import Dict, Optional

from app.core.domain.cart import Cart
from app.core.repositories.cart_repository import CartRepository


class FakeCartRepository(CartRepository):
    """In-memory CartRepository for core-layer BDD scenarios."""

    def __init__(self) -> None:
        self._carts: Dict[str, Cart] = {}

    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        return self._carts.get(user_id)

    def save(self, cart: Cart) -> None:
        self._carts[cart.user_id] = cart
