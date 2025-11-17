"""
API 統一回應格式

定義標準化的 API 回應結構，提供一致的前端接口。
"""
from typing import TypeVar, Generic, Optional
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    統一 API 回應格式
    
    所有 API 端點都應該使用此格式返回數據，確保前端可以統一處理。
    
    Attributes:
        success: 請求是否成功
        code: 業務狀態碼（可自定義）
        message: 回應訊息
        data: 實際的回應資料（泛型）
        timestamp: 時間戳
    
    Example:
        >>> response = ApiResponse(
        ...     success=True,
        ...     code=200,
        ...     message="操作成功",
        ...     data={"user_id": "123"}
        ... )
    """
    success: bool = Field(..., description="請求是否成功")
    code: int = Field(..., description="業務狀態碼")
    message: str = Field(..., description="回應訊息")
    data: Optional[T] = Field(None, description="回應資料")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "code": 200,
                "message": "操作成功",
                "data": {
                    "user_id": "user123",
                    "items": []
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class PaginatedData(BaseModel, Generic[T]):
    """
    分頁數據結構
    
    用於包裝分頁查詢的結果。
    
    Attributes:
        items: 當前頁的項目列表
        total: 總項目數
        page: 當前頁碼（從 1 開始）
        page_size: 每頁項目數
        total_pages: 總頁數
    """
    items: list[T] = Field(..., description="當前頁的項目列表")
    total: int = Field(..., ge=0, description="總項目數")
    page: int = Field(..., ge=1, description="當前頁碼（從 1 開始）")
    page_size: int = Field(..., ge=1, description="每頁項目數")
    total_pages: int = Field(..., ge=0, description="總頁數")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [{"id": 1, "name": "Item 1"}],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10
            }
        }


class ErrorDetail(BaseModel):
    """
    錯誤詳情
    
    提供結構化的錯誤信息。
    """
    field: Optional[str] = Field(None, description="出錯的欄位名稱")
    message: str = Field(..., description="錯誤訊息")
    code: Optional[str] = Field(None, description="錯誤代碼")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "email",
                "message": "Email 格式不正確",
                "code": "INVALID_EMAIL"
            }
        }


class ErrorResponse(BaseModel):
    """
    錯誤回應格式
    
    用於返回錯誤信息的標準格式。
    
    Attributes:
        success: 永遠為 False
        code: HTTP 狀態碼或自定義錯誤碼
        message: 錯誤訊息
        errors: 詳細的錯誤列表（可選）
        timestamp: 時間戳
    """
    success: bool = Field(default=False, description="永遠為 False")
    code: int = Field(..., description="錯誤狀態碼")
    message: str = Field(..., description="錯誤訊息")
    errors: Optional[list[ErrorDetail]] = Field(None, description="詳細錯誤列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "code": 400,
                "message": "請求參數錯誤",
                "errors": [
                    {
                        "field": "email",
                        "message": "Email 格式不正確",
                        "code": "INVALID_EMAIL"
                    }
                ],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

