from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_cart_service
from app.api.schemas.cart import CartOut, AddItemIn
from app.api.utils.converters.cart import cart_out_from_domain
from app.core.services.cart_service import CartService

router = APIRouter(tags=["cart"])


@router.get("/cart", response_model=CartOut)
def get_cart(
    user_id: str,
    service: CartService = Depends(get_cart_service),
):
    cart = service.get_cart(user_id)
    return cart_out_from_domain(cart)


@router.post("/cart/items", response_model=CartOut)
def add_item(
    user_id: str,
    body: AddItemIn,
    service: CartService = Depends(get_cart_service),
):
    try:
        cart = service.add_item(
            user_id=user_id,
            product_id=body.product_id,
            unit_price=body.unit_price,
            quantity=body.quantity,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return cart_out_from_domain(cart)

