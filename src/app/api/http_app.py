"""
HTTP 介面層

只負責 FastAPI 應用程式的 HTTP 相關配置：
- FastAPI 應用實例創建
- 路由註冊
- Middleware 配置
- CORS 配置
- 全局異常處理
等 HTTP 層面的設定

不包含：
- 資料庫初始化（應在應用層處理）
- 業務邏輯（應在服務層處理）
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api import carts
from app.api.schemas.response import ErrorDetail
from app.api.utils.response import (
    error_response,
    validation_error_response,
    internal_error_response,
)


def create_http_app() -> FastAPI:
    """
    創建 FastAPI HTTP 應用程式
    
    只負責 HTTP 層面的配置，包括：
    - 路由註冊
    - 全局異常處理器
    - 中間件配置
    
    :return: FastAPI 應用實例
    """
    app = FastAPI(
        title="Cart Service",
        version="1.0.0",
        description="基於 Clean Architecture 的購物車服務",
    )

    # 註冊全局異常處理器
    register_exception_handlers(app)

    # 註冊路由
    app.include_router(carts.router, prefix="/api")

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    註冊全局異常處理器
    
    統一處理各種異常，返回標準化的錯誤回應。
    
    Args:
        app: FastAPI 應用實例
    """
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """
        處理請求驗證錯誤（422）
        
        當 Pydantic 驗證失敗時觸發。
        """
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])  # 跳過 "body"
            errors.append(
                ErrorDetail(
                    field=field or None,
                    message=error["msg"],
                    code=error["type"]
                )
            )
        
        error_resp = validation_error_response(
            message="輸入驗證失敗",
            errors=errors
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_resp.model_dump()
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(
        request: Request,
        exc: ValidationError
    ) -> JSONResponse:
        """
        處理 Pydantic 驗證錯誤
        
        當內部 Pydantic 模型驗證失敗時觸發。
        """
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(
                ErrorDetail(
                    field=field or None,
                    message=error["msg"],
                    code=error["type"]
                )
            )
        
        error_resp = validation_error_response(
            message="數據驗證失敗",
            errors=errors
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_resp.model_dump()
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exc: ValueError
    ) -> JSONResponse:
        """
        處理 ValueError（400）
        
        通常是業務邏輯驗證失敗時拋出。
        """
        error_resp = error_response(
            message="請求參數錯誤",
            code=400,
            errors=[ErrorDetail(message=str(exc))]
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_resp.model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """
        處理所有未捕獲的異常（500）
        
        作為最後的保障，防止錯誤信息洩露。
        """
        # 在開發環境可以顯示詳細錯誤
        # 在生產環境應該隱藏詳細信息
        import os
        is_debug = os.getenv("DEBUG", "false").lower() == "true"
        
        detail = str(exc) if is_debug else None
        
        error_resp = internal_error_response(
            message="伺服器內部錯誤",
            detail=detail
        )
        
        # 記錄錯誤日誌（實際應用中應使用 logging）
        print(f"[ERROR] Unhandled exception: {exc}")
        if is_debug:
            import traceback
            traceback.print_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_resp.model_dump()
        )

