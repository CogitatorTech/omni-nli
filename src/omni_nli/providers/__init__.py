"""NLI provider implementations for Omni-NLI.

This package contains provider classes for different NLI backends:
Ollama (local), HuggingFace (local/API), and OpenRouter (API).
"""

from .base import NLIProvider, NLIResult
from .factory import get_provider, list_available_providers

__all__ = [
    "NLIProvider",
    "NLIResult",
    "get_provider",
    "list_available_providers",
]
