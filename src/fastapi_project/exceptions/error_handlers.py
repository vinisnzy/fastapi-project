import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_project.exceptions.exceptions import AppException

logger = logging.getLogger(__name__)


def error_log_fields(request: Request, code: str, status: int) -> dict[str, Any]:
    return {
        "event": "request_error",
        "error_code": code,
        "status_code": status,
        "path": request.url.path,
        "method": request.method,
        "request_id": getattr(request.state, "request_id", None),
    }


ERROR_CODE_BY_STATUS = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def build_error_response(
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": error_code,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if details:
        error["details"] = details
    if request_id:
        error["request_id"] = request_id
    return {"success": False, "error": error}


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    if not getattr(exc, "already_logged", False):
        reason = getattr(exc, "log_reason", None) or {
            "Not authenticated": "missing_credentials",
            "Token expired": "access_token_expired",
            "Invalid token": "invalid_access_token",
            "Invalid refresh token": "invalid_refresh_token",
            "Refresh token revoked": "revoked_refresh_token",
            "Invalid credentials": "invalid_credentials",
        }.get(exc.message)
        logger.warning(
            "Application error",
            extra={
                **error_log_fields(request, exc.error_code, exc.status_code),
                **({"reason": reason} if reason else {}),
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(exc.error_code, exc.message, exc.details),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    logger.warning(
        "Request validation failed",
        extra=error_log_fields(request, "VALIDATION_ERROR", 422),
    )
    return JSONResponse(
        status_code=422,
        content=build_error_response(
            "VALIDATION_ERROR", "Request validation failed", {"errors": errors}
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = ERROR_CODE_BY_STATUS.get(exc.status_code, "HTTP_ERROR")
    logger.warning("HTTP error", extra=error_log_fields(request, code, exc.status_code))
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(code, str(exc.detail)),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        extra={
            **error_log_fields(request, "INTERNAL_ERROR", 500),
            "exception_type": type(exc).__name__,
        },
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content=build_error_response(
            "INTERNAL_ERROR", "An unexpected error occurred. Please try again later."
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
