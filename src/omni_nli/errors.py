"""Error types and codes for Omni-NLI tool operations.

This module defines error codes and custom exception classes used
throughout the application for consistent error handling.
"""

from dataclasses import dataclass, field
from enum import Enum


class ErrorCode(str, Enum):
    """Enumeration of error codes used throughout the application.

    Each code represents a specific type of error that can occur
    during tool execution or API request processing.
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"


@dataclass
class ToolError:
    """Data class representing a tool execution error.

    Attributes:
        code: The error code identifying the error type.
        message: Human-readable error message.
        details: Optional additional error details.
    """

    code: ErrorCode
    message: str
    details: object | None = None


@dataclass
class ToolLogicError(Exception):
    """Exception raised when a tool encounters a logic error.

    This exception wraps a ToolError and can be raised during
    tool execution to signal errors to the caller.

    Attributes:
        code: The error code identifying the error type.
        message: Human-readable error message.
        details: Optional additional error details.
        error: The wrapped ToolError instance (auto-generated).
    """

    code: ErrorCode
    message: str
    details: object | None = None
    error: ToolError = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the wrapped ToolError after dataclass initialization."""
        self.error = ToolError(
            code=self.code,
            message=self.message,
            details=self.details,
        )
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a formatted string representation of the error."""
        if self.details:
            return f"{self.code.value}: {self.message} - {self.details}"
        return f"{self.code.value}: {self.message}"
