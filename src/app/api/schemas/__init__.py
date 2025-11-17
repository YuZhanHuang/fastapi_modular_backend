"""
API Schema 定義

按資源組織所有 API 層的 Request/Response Schema。
"""
from app.api.schemas.response import (
    ApiResponse,
    ErrorResponse,
    ErrorDetail,
    PaginatedData,
)

__all__ = [
    "ApiResponse",
    "ErrorResponse",
    "ErrorDetail",
    "PaginatedData",
]

