"""Pydantic models for Omni-NLI API requests and responses.

This module defines the data models used for REST API validation,
serialization, and OpenAPI documentation generation.
"""

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class NLIResultResponse(BaseModel):
    """Response model for NLI evaluation results.

    Contains the classification label, confidence score, and optional
    reasoning trace from models that support extended thinking.
    """

    label: Literal["entailment", "contradiction", "neutral"] = Field(
        ..., description="The predicted NLI label."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the prediction (0-1)."
    )
    thinking_trace: Optional[str] = Field(
        None, description="The reasoning trace from models that support extended thinking."
    )
    model: str = Field(..., description="The model that was used for evaluation.")
    backend: str = Field(..., description="The backend provider that was used.")


class JsonContentBlock(BaseModel):
    """A content block containing JSON data for tool responses."""

    type: str = Field("json", description="The type of the content block.", examples=["json"])
    data: Any = Field(
        ...,
        description="The structured JSON payload.",
        examples=[{"label": "entailment", "confidence": 0.95}],
    )


class ToolResponse(BaseModel):
    """Response wrapper for MCP tool calls containing content blocks."""

    content: List[JsonContentBlock] = Field(
        ..., description="A list of content blocks containing the tool's output."
    )


class ErrorDetail(BaseModel):
    """Detailed error information for validation and other errors."""

    loc: List[str] = Field(..., description="The location of the error (e.g., the field name).")
    msg: str = Field(..., description="A human-readable message for the specific error.")
    type: str = Field(..., description="The type of the error.")


class ErrorBody(BaseModel):
    """Structured error body with code, message, and optional details."""

    code: str = Field(
        ...,
        description="A unique code for the error type (e.g., 'VALIDATION_ERROR').",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="A high-level, human-readable error message.",
        examples=["Input validation failed."],
    )
    details: Any = Field(
        None, description="Optional details about the error (validation errors or other context)."
    )


class ErrorResponse(BaseModel):
    """Standard error response wrapper for API errors."""

    error: ErrorBody


class ToolDefinition(BaseModel):
    """Definition of an available MCP tool with its schema."""

    name: str = Field(..., examples=["evaluate_nli"])
    title: str = Field(..., examples=["Evaluate NLI Logic"])
    description: str = Field(
        ...,
        examples=[
            "Analyzes a premise and hypothesis to determine entailment, contradiction, or neutral."
        ],
    )
    inputSchema: dict = Field(
        ...,
        examples=[
            {
                "type": "object",
                "properties": {
                    "premise": {"type": "string"},
                    "hypothesis": {"type": "string"},
                },
                "required": ["premise", "hypothesis"],
            }
        ],
    )


class ToolListResponse(BaseModel):
    """Response containing a list of available tools."""

    tools: List[ToolDefinition]


class ProviderInfo(BaseModel):
    """Configuration and status information for an NLI provider."""

    host: Optional[str] = Field(None, description="Host URL for local providers like Ollama.")
    token_configured: Optional[bool] = Field(
        None,
        description="Whether an access token or API key is configured for this provider.",
    )
    cache_dir: Optional[str] = Field(
        None,
        description="Cache directory for local model artifacts, if applicable.",
    )
    default_model: str = Field(
        ...,
        description="Default model name used when no explicit model is provided.",
    )


class ProvidersResponse(BaseModel):
    """Response containing information about all available providers."""

    ollama: ProviderInfo
    huggingface: ProviderInfo
    openrouter: ProviderInfo
    default_backend: str = Field(..., description="Default backend for NLI evaluation.")
