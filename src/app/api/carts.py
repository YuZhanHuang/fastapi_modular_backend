from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_cart_service
from app.api.schemas.cart import CartOut, AddItemIn
from app.api.schemas.response import ApiResponse
from app.api.utils.converters.cart import cart_out_from_domain
from app.api.utils.response import success_response, created_response, not_found_response
from app.core.services.cart_service import CartService

router = APIRouter(tags=["cart"])


@router.get(
    "/cart",
    response_model=ApiResponse[CartOut],
    summary="獲取購物車",
    description="根據用戶 ID 獲取購物車內容"
)
def get_cart(
    user_id: str,
    service: CartService = Depends(get_cart_service),
) -> ApiResponse[CartOut]:
    """
    獲取購物車
    
    Args:
        user_id: 用戶 ID
        service: 購物車服務（自動注入）
    
    Returns:
        包含購物車信息的標準化回應
    
    Raises:
        HTTPException: 當購物車不存在時返回 404
    """
    cart = service.get_cart(user_id)
    
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_response(
                resource_type="購物車",
                resource_id=user_id
            ).model_dump()
        )
    
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
    service: CartService = Depends(get_cart_service),
) -> ApiResponse[CartOut]:
    """
    加入購物車項目
    
    Args:
        user_id: 用戶 ID
        body: 商品信息
        service: 購物車服務（自動注入）
    
    Returns:
        包含更新後購物車信息的標準化回應
    
    Raises:
        HTTPException: 當輸入驗證失敗或業務規則違反時返回 400
    """
    try:
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
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

