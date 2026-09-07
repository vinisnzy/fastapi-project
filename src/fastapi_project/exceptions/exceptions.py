from typing import Any
from uuid import UUID


class AppException(Exception):
    """Base exception for all application errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found"""

    def __init__(
        self, resource: str, resource_id: UUID | None = None, message: str | None = None
    ) -> None:
        details = {"resource": resource}
        if resource_id:
            details["resource_id"] = str(resource_id)
        super().__init__(
            message=message or f"{resource} not found with id: {resource_id}",
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class UnauthorizedError(AppException):
    """Missing or invalid credentials"""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED")


class ForbiddenError(AppException):
    """Authenticated but not allowed"""

    def __init__(self, message: str = "Not enough permissions") -> None:
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN")


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=409, error_code="CONFLICT")
