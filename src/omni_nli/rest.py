import json
import logging

from pydantic import ValidationError
from spectree import Response, SpecTree
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .api_models import (
    ErrorBody,
    ErrorResponse,
    ModelsResponse,
    NLIResultResponse,
    ProvidersResponse,
)
from .errors import ErrorCode, ToolLogicError
from .providers import get_provider, list_available_providers
from .settings import settings
from .tools import EvaluateNLIArgs

_logger = logging.getLogger(__name__)

api_spec = SpecTree(
    "starlette",
    title="Omni-NLI REST API",
    description="Clean REST API for natural language inference (NLI).",
    version=settings.pkg_version,
    mode="strict",
    swagger_url="/docs",
    redoc_url="/redoc",
    naming_strategy=lambda model: model.__name__,
    servers=[{"url": "/api/v1"}],
)


def _error(code: str, message: str, details=None, status_code: int = 400) -> JSONResponse:
    error_body = ErrorBody(code=code, message=message, details=details)
    payload = ErrorResponse(error=error_body)
    return JSONResponse(payload.model_dump(), status_code=status_code)


async def _parse_json_body(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")

    if "application/json" not in content_type:
        raise ValueError("Unsupported Content-Type. Use application/json.")

    # DoS protection: limit body size to 10MB
    if int(request.headers.get("content-length", 0)) > 10 * 1024 * 1024:
        raise ValueError("Request payload too large (limit: 10MB).")

    body = await request.body()
    if len(body) > 10 * 1024 * 1024:
        raise ValueError("Request payload too large (limit: 10MB).")

    return json.loads(body) if body else {}


@api_spec.validate(
    resp=Response(
        HTTP_200=NLIResultResponse,
        HTTP_400=ErrorResponse,
        HTTP_404=ErrorResponse,
        HTTP_502=ErrorResponse,
        HTTP_500=ErrorResponse,
    ),
    tags=["NLI"],
)
async def evaluate_nli(request: Request) -> JSONResponse:
    """Evaluate the logical relationship between premise and hypothesis."""
    try:
        data = await _parse_json_body(request)
        args = EvaluateNLIArgs(**data)

        provider = await get_provider(backend=args.backend)

        use_reasoning = args.use_reasoning
        if use_reasoning and not provider.supports_reasoning:
            # Clean REST: explicit client feedback rather than silent downgrade
            return _error(
                code=ErrorCode.BAD_REQUEST.value,
                message=f"Backend '{provider.name}' does not support reasoning.",
                status_code=400,
            )

        result = await provider.evaluate(
            premise=args.premise,
            hypothesis=args.hypothesis,
            context=args.context,
            model=args.model,
            use_reasoning=use_reasoning,
        )

        response_data = NLIResultResponse(**result.model_dump())
        return JSONResponse(response_data.model_dump())

    except ValidationError as e:
        return _error(
            code=ErrorCode.VALIDATION_ERROR.value,
            message="Input validation failed.",
            details=e.errors(),
            status_code=400,
        )
    except (json.JSONDecodeError, ValueError) as e:
        return _error(code=ErrorCode.BAD_REQUEST.value, message=str(e), status_code=400)
    except ToolLogicError as e:
        # Should be rare here, but keep mapping consistent.
        status = 500
        if e.code in (ErrorCode.UNKNOWN_TOOL, ErrorCode.NOT_FOUND):
            status = 404
        elif e.code in (ErrorCode.VALIDATION_ERROR, ErrorCode.BAD_REQUEST):
            status = 400
        elif e.code == ErrorCode.PROVIDER_ERROR:
            status = 502
        return _error(
            code=str(e.code.value), message=e.message, details=e.details, status_code=status
        )
    except Exception as e:
        _logger.error(f"Unexpected error in evaluate_nli: {e}", exc_info=True)
        return _error(
            code=ErrorCode.INTERNAL_ERROR.value,
            message="An internal server error occurred.",
            status_code=500,
        )


@api_spec.validate(resp=Response(HTTP_200=ProvidersResponse), tags=["Providers"])
async def providers(request: Request) -> JSONResponse:
    data = list_available_providers()
    response_data = ProvidersResponse(
        **data,
        default_backend=settings.default_backend,
        default_model=settings.default_model,
    )
    return JSONResponse(response_data.model_dump())


@api_spec.validate(
    resp=Response(HTTP_200=ModelsResponse, HTTP_400=ErrorResponse, HTTP_404=ErrorResponse),
    tags=["Models"],
)
async def list_models(request: Request) -> JSONResponse:
    backend = request.query_params.get("backend")
    if not backend:
        return _error(
            code=ErrorCode.BAD_REQUEST.value,
            message="Missing required query parameter: backend",
            status_code=400,
        )

    if backend not in ("ollama", "huggingface", "openrouter"):
        return _error(
            code=ErrorCode.BAD_REQUEST.value,
            message=f"Unknown backend: {backend}",
            status_code=400,
        )

    try:
        provider = await get_provider(backend=backend)  # type: ignore[arg-type]
        models = await provider.list_models()
        response_data = ModelsResponse(backend=backend, models=models)
        return JSONResponse(response_data.model_dump())
    except ValueError as e:
        return _error(code=ErrorCode.PROVIDER_ERROR.value, message=str(e), status_code=502)


def setup_rest_routes() -> list[Route]:
    return [
        Route("/nli/evaluate", endpoint=evaluate_nli, methods=["POST"]),
        Route("/providers", endpoint=providers, methods=["GET"]),
        Route("/models", endpoint=list_models, methods=["GET"]),
    ]
