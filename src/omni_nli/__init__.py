from importlib.metadata import PackageNotFoundError, metadata, version

from .settings import settings

try:
    __version__ = version("omni-nli")
    _meta = metadata("omni-nli")
    __app_name__ = _meta["Name"]
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
    __app_name__ = "omni-nli"

__all__ = ["__app_name__", "__version__", "settings"]
