from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict, Optional

class WaylineError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

def wayline_error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )

async def wayline_exception_handler(request: Request, exc: WaylineError) -> JSONResponse:
    return wayline_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 422:
        code = "UNPROCESSABLE_ENTITY"
        
    return wayline_error_response(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code,
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first_msg = errors[0].get("msg", "Invalid request body or query parameter") if errors else "Validation error"
    return wayline_error_response(
        code="VALIDATION_ERROR",
        message=first_msg,
        status_code=422,
        details={"validation_errors": errors},
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return wayline_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please try again later.",
        status_code=500,
        details={"type": exc.__class__.__name__},
    )

