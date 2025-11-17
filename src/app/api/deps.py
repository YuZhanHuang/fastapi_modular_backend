"""
FastAPI 依賴注入函數

使用新的自動化機制創建 Service 實例。
"""
from fastapi import Depends

from app.infra.db.session import get_session
from app.infra.wiring import get_service
from app.core.services.cart_service import CartService


def get_cart_service(
    session=Depends(get_session),
) -> CartService:
    """
    獲取 CartService 實例
    使用自動化機制，無需手動組裝依賴
    """
    return get_service(CartService, session)





