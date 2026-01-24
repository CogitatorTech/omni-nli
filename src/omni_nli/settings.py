from importlib.metadata import PackageNotFoundError, version

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_pkg_version() -> str:
    try:
        return version("omni-nli")
    except PackageNotFoundError:
        return "0.0.0"


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    pkg_version: str = get_pkg_version()
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"

    ollama_host: str = "http://localhost:11434"
    huggingface_token: str | None = None
    hf_cache_dir: str | None = None
    openrouter_api_key: str | None = None

    default_backend: str = "ollama"
    default_model: str = "llama3.2"

    max_thinking_tokens: int = 4096
    max_total_tokens: int = 8192

    provider_cache_size: int = 8


settings = ServerSettings()
