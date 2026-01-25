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

Edit the .env file to set up your preferred backends:

```bash
# Server Configuration
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO

# Backend Providers
# 1. Ollama (Local)
OLLAMA_HOST=http://localhost:11434

# 2. HuggingFace (Local)
HUGGINGFACE_TOKEN=your_hf_token  # Optional if using public gated models

# 3. OpenRouter (Cloud)
OPENROUTER_API_KEY=your_sk_key

# Defaults
DEFAULT_BACKEND=ollama
DEFAULT_MODEL=llama3.2
```

## Running the Server

Start the server using the CLI command:

```bash
omni-nli
```

Or override settings via CLI arguments:

```bash
omni-nli --port 8080 --default-backend openrouter --default-model anthropic/claude-3-5-sonnet
```

The server will start at http://127.0.0.1:8000 (by default).

## Next Steps

- Check the [Examples](examples.md) to see how to make requests.
- Explore the [API Reference](api-reference.md) for full endpoint details.
