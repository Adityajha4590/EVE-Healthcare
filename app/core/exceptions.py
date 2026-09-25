class AppException(Exception):
    """Base exception for domain-level errors.

    Subclasses are caught by the global exception handler in main.py
    and mapped to appropriate HTTP responses.
    """

    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundException(AppException):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail=detail, status_code=404)


class ConflictException(AppException):
    """Conflicting state (409)."""

    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(detail=detail, status_code=409)


class ForbiddenException(AppException):
    """Insufficient permissions (403)."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail=detail, status_code=403)


class UnauthorizedException(AppException):
    """Authentication required or invalid (401)."""

    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(detail=detail, status_code=401)
