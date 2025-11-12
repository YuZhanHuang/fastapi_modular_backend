"""
Cart Domain Model 到 API Schema 的轉換器

負責將 core/domain 的 Cart 模型轉換為 API 層的 Schema。
"""
from app.core.domain.cart import Cart, CartItem
from app.api.schemas.cart import CartOut, CartItemOut


def cart_item_out_from_domain(item: CartItem) -> CartItemOut:
    """
    將 Domain CartItem 轉換為 API CartItemOut
    
    :param item: Domain 層的 CartItem
    :return: API 層的 CartItemOut
    """
    return CartItemOut(
        product_id=item.product_id,
        quantity=item.quantity,
        unit_price=item.unit_price,
    )


def cart_out_from_domain(cart: Cart) -> CartOut:
    """
    將 Domain Cart 轉換為 API CartOut
    
    :param cart: Domain 層的 Cart
    :return: API 層的 CartOut
    """
    return CartOut(
        user_id=cart.user_id,
        items=[cart_item_out_from_domain(item) for item in cart.items],
        total=cart.total_amount(),
    )

