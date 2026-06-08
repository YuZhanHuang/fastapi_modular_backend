from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import inject_service
from app.api.schemas.cart import CartOut, AddItemIn
from app.api.schemas.response import ApiResponse
from app.api.utils.converters.cart import cart_out_from_domain
from app.api.utils.response import success_response, created_response
from app.core.services.cart_service import CartService
from app.infra.containers import get_container

router = APIRouter(tags=["cart"])
container = get_container()

CartServiceDep = Annotated[
    CartService,
    Depends(inject_service(container.services.cart_service)),
]


@router.get(
    "/cart",
    response_model=ApiResponse[CartOut],
    summary="獲取購物車",
    description="根據用戶 ID 獲取購物車內容"
)
def get_cart(
    user_id: str,
    service: CartServiceDep,
) -> ApiResponse[CartOut]:
    """
    獲取購物車

    Args:
        user_id: 用戶 ID
        service: 購物車服務（自動注入）

    Returns:
        包含購物車信息的標準化回應
    """
    cart = service.get_cart(user_id)
    cart_data = cart_out_from_domain(cart)
    return success_response(
        data=cart_data,
        message="獲取購物車成功"
    )


@router.post(
    "/cart/items",
    response_model=ApiResponse[CartOut],
    status_code=status.HTTP_201_CREATED,
    summary="加入購物車項目",
    description="將商品加入用戶的購物車"
)
def add_item(
    user_id: str,
    body: AddItemIn,
    service: CartServiceDep,
) -> ApiResponse[CartOut]:
    """
    加入購物車項目

    Args:
        user_id: 用戶 ID
        body: 商品信息
        service: 購物車服務（自動注入）

    Returns:
        包含更新後購物車信息的標準化回應
    """
    cart = service.add_item(
        user_id=user_id,
        product_id=body.product_id,
        unit_price=body.unit_price,
        quantity=body.quantity,
    )

    cart_data = cart_out_from_domain(cart)
    return created_response(
        data=cart_data,
        message="商品已成功加入購物車"
    )
