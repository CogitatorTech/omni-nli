# Getting Started

## Installation

### 1. Install via Pip

Clone the repository and install dependencies:

```bash
git clone https://github.com/CogitatorTech/omni-nli.git
cd omni-nli
pip install .
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

# Default backend for NLI evaluation
DEFAULT_BACKEND=huggingface

# Per-provider default models (used when request model is omitted)
OLLAMA_DEFAULT_MODEL=qwen3:8b
HUGGINGFACE_DEFAULT_MODEL=microsoft/Phi-3.5-mini-instruct
OPENROUTER_DEFAULT_MODEL=openai/gpt-5-mini

# Token limits
MAX_THINKING_TOKENS=4096
```

CLI Arguments example:

```bash
omni-nli \
  --host 0.0.0.0 \
  --port 8080 \
  --default-backend openrouter \
  --openrouter-default-model anthropic/claude-3.5-sonnet
```

## Supported Backends

| Backend     | Local | Example Models                                    |
|:------------|:------|:--------------------------------------------------|
| Ollama      | Yes   | qwen3:8b, llama3.2:3b, mistral                    |
| HuggingFace | Yes   | Qwen/Qwen2.5-1.5B-Instruct                         |
| OpenRouter  | No    | deepseek/deepseek-r1, anthropic/claude-3.5-sonnet |

## Running the Server

Start the server using the CLI command:

```bash
omni-nli
```

The server will start at http://127.0.0.1:8000 (by default).

## Next Steps

- Check the [Examples](examples.md) to see how to make requests.
- Explore the [API Reference](api-reference.md) for full endpoint details.
