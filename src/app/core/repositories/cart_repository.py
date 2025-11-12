from abc import ABC, abstractmethod
from typing import Optional

from app.core.domain.cart import Cart


class CartRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[Cart]:
        raise NotImplementedError


    @abstractmethod
    def save(self, cart: Cart) -> None:
        raise NotImplementedError
    


