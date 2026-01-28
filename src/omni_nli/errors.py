from dataclasses import dataclass, field
from enum import Enum


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"


@dataclass
class ToolError:
    code: ErrorCode
    message: str
    details: object | None = None


@dataclass
class ToolLogicError(Exception):
    code: ErrorCode
    message: str
    details: object | None = None
    error: ToolError = field(init=False)

    def __post_init__(self) -> None:
        self.error = ToolError(
            code=self.code,
            message=self.message,
            details=self.details,
        )
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.code.value}: {self.message} - {self.details}"
        return f"{self.code.value}: {self.message}"
