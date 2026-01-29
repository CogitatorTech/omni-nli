import json
import logging

from pydantic import ValidationError
from spectree import Response, SpecTree
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from .api_models import (
    ErrorBody,
    ErrorResponse,
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
    swagger_url="/apidoc/swagger",
    # Some Spectree/starlette plugin versions don't reliably mount ReDoc at custom paths.
    # We provide our own deterministic /apidoc/redoc route below.
    redoc_url=None,
    naming_strategy=lambda model: model.__name__,
    servers=[{"url": "/api/v1"}],
)


def _error(
    code: str, message: str, details: object | None = None, status_code: int = 400
) -> JSONResponse:
    error_body = ErrorBody(code=code, message=message, details=details)
    payload = ErrorResponse(error=error_body)
    return JSONResponse(payload.model_dump(), status_code=status_code)


async def _parse_json_body(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")

    if "application/json" not in content_type:
        raise ValueError("Unsupported Content-Type. Use application/json.")

    # DoS protection: limit body size to 10MB
    max_body_size = 10 * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > max_body_size:
        raise ValueError("Request payload too large (limit: 10MB).")

    body = await request.body()
    if len(body) > max_body_size:
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

        result = await provider.evaluate(
            premise=args.premise,
            hypothesis=args.hypothesis,
            context=args.context,
            model=args.model,
            use_reasoning=args.use_reasoning,
        )

        response_data = NLIResultResponse(**result.model_dump())
        return JSONResponse(response_data.model_dump(exclude_none=True))

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
    )
    return JSONResponse(response_data.model_dump())


async def redoc(request: Request) -> HTMLResponse:
    """Serve ReDoc at a deterministic URL: /api/v1/apidoc/redoc."""
    # Spectree exposes the OpenAPI JSON at /api/v1/apidoc/openapi.json in this project.
    # Use a relative URL so it works behind proxies and with the /api/v1 mount.
    openapi_url = "./openapi.json"

    html = f"""<!doctype html>
<html>
  <head>
    <meta charset='utf-8'/>
    <title>Omni-NLI API Docs</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
  </head>
  <body>
    <redoc spec-url='{openapi_url}'></redoc>
    <script src='https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js'></script>
  </body>
</html>"""

    return HTMLResponse(html)


def setup_rest_routes() -> list[Route]:
    return [
        Route("/nli/evaluate", endpoint=evaluate_nli, methods=["POST"]),
        Route("/providers", endpoint=providers, methods=["GET"]),
        Route("/apidoc/redoc", endpoint=redoc, methods=["GET"]),
    ]
