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
    async with session_manager.run():
        _logger.info("Omni-NLI started with StreamableHTTP session manager.")
        try:
            yield
        finally:
            _logger.info("Omni-NLI shutting down...")


starlette_app = Starlette(debug=True, lifespan=lifespan)


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
@click.option("--host", default=None, help="The host to bind to.", envvar="HOST")
@click.option("--port", default=None, type=int, help="The port to bind to.", envvar="PORT")
@click.option("--log-level", default=None, help="The log level to use.", envvar="LOG_LEVEL")
@click.option(
    "--ollama-host",
    default=None,
    help="Ollama server URL.",
    envvar="OLLAMA_HOST",
)
@click.option(
    "--default-backend",
    default=None,
    help="Default backend provider (valid values: ollama, huggingface, or openrouter).",
    envvar="DEFAULT_BACKEND",
)
@click.option(
    "--default-model",
    default=None,
    help="Default model to use for NLI evaluation.",
    envvar="DEFAULT_MODEL",
)
def main(
    host: str | None,
    port: int | None,
    log_level: str | None,
    ollama_host: str | None,
    default_backend: str | None,
    default_model: str | None,
) -> int:
    import uvicorn

    if host:
        settings.host = host
    if port:
        settings.port = port
    if log_level:
        settings.log_level = log_level
    if ollama_host:
        settings.ollama_host = ollama_host
    if default_backend:
        settings.default_backend = default_backend
    if default_model:
        settings.default_model = default_model

    setup_logging(settings.log_level)
    _logger.info("Setting up cache...")
    setup_cache()

    _logger.info(f"Starting Omni-NLI server on {settings.host}:{settings.port}")
    uvicorn.run(starlette_app, host=settings.host, port=settings.port)
    return 0


if __name__ == "__main__":
    main()
