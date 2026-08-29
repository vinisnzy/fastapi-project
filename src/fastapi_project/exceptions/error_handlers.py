import logging
import traceback
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_project.exceptions.exceptions import AppException

logger = logging.getLogger(__name__)

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
    logger.warning(
        "Application error: %s - %s",
        exc.error_code,
        exc.message,
        extra={"path": request.url.path, "method": request.method},
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
    logger.warning("Validation error on %s", request.url.path)
    return JSONResponse(
        status_code=422,
        content=build_error_response(
            "VALIDATION_ERROR", "Request validation failed", {"errors": errors}
        ),
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            ERROR_CODE_BY_STATUS.get(exc.status_code, "HTTP_ERROR"), str(exc.detail)
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception: %s: %s",
        type(exc).__name__,
        exc,
        extra={"path": request.url.path, "traceback": traceback.format_exc()},
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
