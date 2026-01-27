# Getting Started

## Installation

### 1. Install via Pip

Access the package from PyPI (coming soon) or install directly from source:

```bash
pip install omni-nli
```

### 2. Configure Environment

Omni-NLI uses environment variables for configuration. You can create a .env file in your working directory.

Copy the example configuration:

```bash
cp .env.example .env
```

Edit the .env file to set up your preferred backends.

## Configuration Reference

All settings can be configured via environment variables or CLI arguments.

```bash
# Server settings
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO

# Backend configuration
OLLAMA_HOST=http://localhost:11434

# HuggingFace (optional; token is needed for gated models)
HUGGINGFACE_TOKEN=

# OpenRouter (optional)
OPENROUTER_API_KEY=

# Default backend and model for NLI evaluation
DEFAULT_BACKEND=ollama
# Example (Ollama): qwen3:8b
DEFAULT_MODEL=qwen3:8b

# Token limits
MAX_THINKING_TOKENS=4096
MAX_TOTAL_TOKENS=8192
```

!!! note
    `DEFAULT_MODEL` is backend-specific. For example:

    - Ollama: `qwen3:8b`, `llama3.2:3b`
    - HuggingFace: `microsoft/Phi-3.5-mini-instruct` (token only needed for gated models)
    - OpenRouter: `deepseek/deepseek-r1` (reasoning), `openai/gpt-4o-mini` (standard)

CLI Arguments example:

```bash
omni-nli --host 0.0.0.0 --port 8080 --default-backend openrouter --default-model anthropic/claude-3.5-sonnet
```

## Supported Backends

| Backend     | Local | Reasoning Support | Example Models                                    |
|:------------|:------|:------------------|:--------------------------------------------------|
| Ollama      | Yes   | No                | llama3.2, mistral, qwen2.5                        |
| HuggingFace | Yes   | No                | meta-llama/Llama-3.2-3B-Instruct                  |
| OpenRouter  | No    | Yes               | anthropic/claude-3.5-sonnet, deepseek/deepseek-r1 |

## Running the Server

Start the server using the CLI command:

```bash
omni-nli
```

The server will start at http://127.0.0.1:8000 (by default).

## Next Steps

- Check the [Examples](examples.md) to see how to make requests.
- Explore the [API Reference](api-reference.md) for full endpoint details.
