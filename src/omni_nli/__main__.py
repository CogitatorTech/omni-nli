import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import click
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from pythonjsonlogger import jsonlogger
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .event_store import InMemoryEventStore
from .mcp import app as mcp_app
from .settings import settings
from .tools import setup_cache, setup_tools

_logger = logging.getLogger(__name__)


def setup_logging(log_level: str) -> None:
    level = logging.getLevelName(log_level.upper())
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    logHandler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[logHandler])
    _logger.info(f"Logging configured with level: {log_level.upper()}")


async def health_check(_request: Request) -> JSONResponse:
    _logger.debug("Health check requested.")
    return JSONResponse({"status": "ok", "version": settings.pkg_version})


event_store = InMemoryEventStore()
session_manager = StreamableHTTPSessionManager(app=mcp_app, event_store=event_store)


async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncGenerator[None, None]:
    async with session_manager.run():  # type: ignore[attr-defined]
        _logger.info("Omni-NLI started with StreamableHTTP session manager.")
        try:
            yield
        finally:
            _logger.info("Omni-NLI shutting down...")


starlette_app = Starlette(debug=settings.debug, lifespan=lifespan)


def setup_app_routes(main_app: Starlette) -> None:
    from .rest import api_spec, setup_rest_routes

    api_v1_app = Starlette()
    api_v1_app.router.routes.extend(setup_rest_routes())

    api_spec.register(api_v1_app)

    health_route = Route("/api/health", endpoint=health_check, methods=["GET"])

    main_app.routes.extend(
        [
            Mount("/mcp/", app=handle_streamable_http),
            health_route,
            Mount("/api/v1", app=api_v1_app),
        ]
    )


setup_tools()
setup_app_routes(starlette_app)

starlette_app = CORSMiddleware(
    starlette_app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    expose_headers=["Mcp-Session-Id"],
)


@click.command()
@click.option(
    "--host",
    default=settings.host,
    show_default=True,
    help="The host to bind to.",
    envvar="HOST",
)
@click.option(
    "--port",
    default=settings.port,
    show_default=True,
    type=int,
    help="The port to bind to.",
    envvar="PORT",
)
@click.option(
    "--log-level",
    default=settings.log_level,
    show_default=True,
    help="The log level to use.",
    envvar="LOG_LEVEL",
)
@click.option(
    "--debug/--no-debug",
    is_flag=True,
    default=settings.debug,
    show_default=True,
    help="Enable debug mode (detailed error tracebacks).",
    envvar="DEBUG",
)
@click.option(
    "--ollama-host",
    default=settings.ollama_host,
    show_default=True,
    help="Ollama server URL.",
    envvar="OLLAMA_HOST",
)
@click.option(
    "--default-backend",
    default=settings.default_backend,
    show_default=True,
    type=click.Choice(["ollama", "huggingface", "openrouter"], case_sensitive=False),
    help="Default backend provider.",
    envvar="DEFAULT_BACKEND",
)
@click.option(
    "--ollama-default-model",
    default=settings.ollama_default_model,
    show_default=True,
    help="Default Ollama model to use for NLI evaluation.",
    envvar="OLLAMA_DEFAULT_MODEL",
)
@click.option(
    "--huggingface-default-model",
    default=settings.huggingface_default_model,
    show_default=True,
    help="Default HuggingFace model to use for NLI evaluation.",
    envvar="HUGGINGFACE_DEFAULT_MODEL",
)
@click.option(
    "--openrouter-default-model",
    default=settings.openrouter_default_model,
    show_default=True,
    help="Default OpenRouter model to use for NLI evaluation.",
    envvar="OPENROUTER_DEFAULT_MODEL",
)
@click.option(
    "--openrouter-api-key",
    default=settings.openrouter_api_key,
    show_default=False,
    help="OpenRouter API Key.",
    envvar="OPENROUTER_API_KEY",
)
@click.option(
    "--huggingface-token",
    default=settings.huggingface_token,
    show_default=False,
    help="HuggingFace API Token.",
    envvar="HUGGINGFACE_TOKEN",
)
@click.option(
    "--hf-cache-dir",
    default=settings.hf_cache_dir,
    show_default=True,
    help="HuggingFace models cache directory.",
    envvar="HF_CACHE_DIR",
)
@click.option(
    "--max-thinking-tokens",
    default=settings.max_thinking_tokens,
    show_default=True,
    type=int,
    help="Max tokens for thinking traces.",
    envvar="MAX_THINKING_TOKENS",
)
@click.option(
    "--return-thinking-trace/--no-return-thinking-trace",
    is_flag=True,
    default=settings.return_thinking_trace,
    show_default=True,
    help="Return raw thinking trace in response.",
    envvar="RETURN_THINKING_TRACE",
)
def main(
    host: str,
    port: int,
    log_level: str,
    debug: bool,
    ollama_host: str,
    default_backend: str,
    ollama_default_model: str,
    huggingface_default_model: str,
    openrouter_default_model: str,
    openrouter_api_key: str | None,
    huggingface_token: str | None,
    hf_cache_dir: str | None,
    max_thinking_tokens: int,
    return_thinking_trace: bool,
) -> int:
    import uvicorn

    # Update settings with resolved values from CLI or Env
    settings.host = host
    settings.port = port
    settings.log_level = log_level
    settings.debug = debug
    settings.ollama_host = ollama_host
    settings.default_backend = default_backend
    settings.ollama_default_model = ollama_default_model
    settings.huggingface_default_model = huggingface_default_model
    settings.openrouter_default_model = openrouter_default_model
    settings.openrouter_api_key = openrouter_api_key
    settings.huggingface_token = huggingface_token
    settings.hf_cache_dir = hf_cache_dir
    settings.max_thinking_tokens = max_thinking_tokens
    settings.return_thinking_trace = return_thinking_trace

    setup_logging(settings.log_level)
    _logger.info("Setting up cache...")
    setup_cache()

    _logger.info(f"Starting Omni-NLI server on {settings.host}:{settings.port}")
    uvicorn.run(starlette_app, host=settings.host, port=settings.port)
    return 0


if __name__ == "__main__":
    main()
