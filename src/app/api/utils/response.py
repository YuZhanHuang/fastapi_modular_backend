"""
API 回應包裝工具

提供便捷的函數來創建標準化的 API 回應。
"""
from typing import TypeVar, Optional
from math import ceil

from app.api.schemas.response import (
    ApiResponse,
    ErrorResponse,
    ErrorDetail,
    PaginatedData,
)


T = TypeVar('T')


def success_response(
    data: T,
    message: str = "操作成功",
    code: int = 200
) -> ApiResponse[T]:
    """
    創建成功回應
    
    Args:
        data: 要返回的數據
        message: 成功訊息
        code: 業務狀態碼（默認 200）
    
    Returns:
        標準化的成功回應
    
    Example:
        >>> from app.api.schemas.cart import CartOut
        >>> cart_data = CartOut(user_id="123", items=[], total=0)
        >>> response = success_response(cart_data, "獲取購物車成功")
    """
    return ApiResponse(
        success=True,
        code=code,
        message=message,
        data=data
    )


def created_response(
    data: T,
    message: str = "創建成功"
) -> ApiResponse[T]:
    """
    創建資源創建成功的回應（201）
    
    Args:
        data: 創建的資源數據
        message: 成功訊息
    
    Returns:
        201 狀態的成功回應
    """
    return success_response(data=data, message=message, code=201)


def error_response(
    message: str,
    code: int = 400,
    errors: Optional[list[ErrorDetail]] = None
) -> ErrorResponse:
    """
    創建錯誤回應
    
    Args:
        message: 錯誤訊息
        code: 錯誤狀態碼（默認 400）
        errors: 詳細的錯誤列表
    
    Returns:
        標準化的錯誤回應
    
    Example:
        >>> error = error_response("參數錯誤", code=400)
    """
    return ErrorResponse(
        success=False,
        code=code,
        message=message,
        errors=errors
    )


def paginated_response(
    items: list[T],
    total: int,
    page: int,
    page_size: int,
    message: str = "查詢成功"
) -> ApiResponse[PaginatedData[T]]:
    """
    創建分頁回應
    
    Args:
        items: 當前頁的項目列表
        total: 總項目數
        page: 當前頁碼（從 1 開始）
        page_size: 每頁項目數
        message: 成功訊息
    
    Returns:
        包含分頁信息的標準化回應
    
    Example:
        >>> users = [User(id=1), User(id=2)]
        >>> response = paginated_response(
        ...     items=users,
        ...     total=100,
        ...     page=1,
        ...     page_size=10
        ... )
    """
    total_pages = ceil(total / page_size) if page_size > 0 else 0
    
    paginated_data = PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    return success_response(
        data=paginated_data,
        message=message
    )


def not_found_response(
    message: str = "資源不存在",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> ErrorResponse:
    """
    創建 404 Not Found 錯誤回應
    
    Args:
        message: 錯誤訊息
        resource_type: 資源類型（如 "User", "Order"）
        resource_id: 資源 ID
    
    Returns:
        404 錯誤回應
    
    Example:
        >>> response = not_found_response(
        ...     resource_type="User",
        ...     resource_id="123"
        ... )
    """
    if resource_type and resource_id:
        message = f"{resource_type} (ID: {resource_id}) 不存在"
    elif resource_type:
        message = f"{resource_type} 不存在"
    
    return error_response(message=message, code=404)


def validation_error_response(
    message: str = "輸入驗證失敗",
    errors: Optional[list[ErrorDetail]] = None
) -> ErrorResponse:
    """
    創建驗證錯誤回應（422）
    
    Args:
        message: 錯誤訊息
        errors: 詳細的驗證錯誤列表
    
    Returns:
        422 驗證錯誤回應
    
    Example:
        >>> errors = [
        ...     ErrorDetail(field="email", message="Email 格式不正確"),
        ...     ErrorDetail(field="name", message="名稱不能為空")
        ... ]
        >>> response = validation_error_response(errors=errors)
    """
    return ErrorResponse(
        success=False,
        code=422,
        message=message,
        errors=errors
    )


def conflict_response(
    message: str = "資源衝突",
    detail: Optional[str] = None
) -> ErrorResponse:
    """
    創建 409 Conflict 錯誤回應
    
    Args:
        message: 錯誤訊息
        detail: 詳細說明
    
    Returns:
        409 衝突錯誤回應
    
    Example:
        >>> response = conflict_response("Email 已被使用")
    """
    errors = None
    if detail:
        errors = [ErrorDetail(message=detail)]
    
    return error_response(message=message, code=409, errors=errors)


def unauthorized_response(
    message: str = "未授權訪問"
) -> ErrorResponse:
    """
    創建 401 Unauthorized 錯誤回應
    
    Args:
        message: 錯誤訊息
    
    Returns:
        401 未授權錯誤回應
    """
    return error_response(message=message, code=401)


def forbidden_response(
    message: str = "禁止訪問"
) -> ErrorResponse:
    """
    創建 403 Forbidden 錯誤回應
    
    Args:
        message: 錯誤訊息
    
    Returns:
        403 禁止訪問錯誤回應
    """
    return error_response(message=message, code=403)


def internal_error_response(
    message: str = "伺服器內部錯誤",
    detail: Optional[str] = None
) -> ErrorResponse:
    """
    創建 500 Internal Server Error 錯誤回應
    
    Args:
        message: 錯誤訊息
        detail: 詳細錯誤信息（生產環境可能不顯示）
    
    Returns:
        500 內部錯誤回應
    """
    errors = None
    if detail:
        errors = [ErrorDetail(message=detail)]
    
    return error_response(message=message, code=500, errors=errors)

