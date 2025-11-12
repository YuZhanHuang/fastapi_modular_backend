from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CartItem:
    """購物車項目（值對象）"""
    product_id: str
    quantity: int
    unit_price: int  # in smallest currency unit, e.g. cents


@dataclass
class Cart:
    """購物車（聚合根）"""
    user_id: str
    items: List[CartItem] = field(default_factory=list)

    def add_item(self, product_id: str, unit_price: int, quantity: int = 1) -> None:
        """添加商品到購物車"""
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        # 查找現有項目並更新數量
        updated_items = []
        found = False
        for item in self.items:
            if item.product_id == product_id:
                # 創建新的不可變對象
                updated_items.append(
                    CartItem(
                        product_id=item.product_id,
                        quantity=item.quantity + quantity,
                        unit_price=item.unit_price
                    )
                )
                found = True
            else:
                updated_items.append(item)
        
        if not found:
            updated_items.append(
                CartItem(product_id=product_id, quantity=quantity, unit_price=unit_price)
            )
        
        self.items = updated_items

    def total_amount(self) -> int:
        """計算購物車總金額"""
        return sum(item.unit_price * item.quantity for item in self.items)


