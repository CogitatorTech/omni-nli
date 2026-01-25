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
HUGGINGFACE_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here

# Default backend and model for NLI evaluation
DEFAULT_BACKEND=ollama
DEFAULT_MODEL=llama3.2

# Token limits
MAX_THINKING_TOKENS=4096
MAX_TOTAL_TOKENS=8192
```

CLI Arguments example:

```bash
omni-nli --host 0.0.0.0 --port 8080 --default-backend openrouter --default-model anthropic/claude-3.5-sonnet
```

## Supported Backends

| Backend | Local | Reasoning Support | Example Models |
| :--- | :--- | :--- | :--- |
| Ollama | Yes | No | llama3.2, mistral, qwen2.5 |
| HuggingFace | Yes | No | meta-llama/Llama-3.2-3B-Instruct |
| OpenRouter | No | Yes | anthropic/claude-3.5-sonnet, deepseek/deepseek-r1 |

## Running the Server

Start the server using the CLI command:

```bash
omni-nli
```

The server will start at http://127.0.0.1:8000 (by default).

## Next Steps

- Check the [Examples](examples.md) to see how to make requests.
- Explore the [API Reference](api-reference.md) for full endpoint details.
