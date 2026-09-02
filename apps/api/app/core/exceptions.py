from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class PravahException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred",
        error_code: str = "BAD_REQUEST",
        meta: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.meta = meta or {}

class UnauthorizedException(PravahException):
    def __init__(self, detail: str = "Authentication required", error_code: str = "UNAUTHORIZED"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, error_code=error_code)

class ForbiddenException(PravahException):
    def __init__(self, detail: str = "Insufficient permissions", error_code: str = "FORBIDDEN"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, error_code=error_code)

class NotFoundException(PravahException):
    def __init__(self, detail: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, error_code=error_code)

class ConflictException(PravahException):
    def __init__(self, detail: str = "Resource conflict", error_code: str = "CONFLICT"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, error_code=error_code)

class PlanLimitExceededException(PravahException):
    def __init__(self, detail: str = "Plan limit reached for this feature. Please upgrade.", error_code: str = "PLAN_LIMIT_EXCEEDED"):
        super().__init__(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=detail, error_code=error_code)

class RateLimitException(PravahException):
    def __init__(self, detail: str = "Too many requests. Please try again later.", error_code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail, error_code=error_code)
