from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class NLIResultResponse(BaseModel):
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
    type: str = Field("json", description="The type of the content block.", examples=["json"])
    data: Any = Field(
        ...,
        description="The structured JSON payload.",
        examples=[{"label": "entailment", "confidence": 0.95}],
    )


class ToolResponse(BaseModel):
    content: List[JsonContentBlock] = Field(
        ..., description="A list of content blocks containing the tool's output."
    )


class ErrorDetail(BaseModel):
    loc: List[str] = Field(..., description="The location of the error (e.g., the field name).")
    msg: str = Field(..., description="A human-readable message for the specific error.")
    type: str = Field(..., description="The type of the error.")


class ErrorBody(BaseModel):
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
    error: ErrorBody


class ToolDefinition(BaseModel):
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
    tools: List[ToolDefinition]


class ProviderInfo(BaseModel):
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
    ollama: ProviderInfo
    huggingface: ProviderInfo
    openrouter: ProviderInfo
    default_backend: str = Field(..., description="Default backend for NLI evaluation.")
