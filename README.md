<div align="center">
  <picture>
    <img alt="Omni-NLI Logo" src="logo.svg" width="200">
  </picture>
<br>

<h2>Omni-NLI</h2>

[![Tests](https://img.shields.io/github/actions/workflow/status/CogitatorTech/omni-nli/tests.yml?label=tests&style=flat&labelColor=333333&logo=github&logoColor=white)](https://github.com/CogitatorTech/omni-nli/actions/workflows/tests.yml)
[![Code Coverage](https://img.shields.io/codecov/c/github/CogitatorTech/omni-nli?style=flat&label=coverage&labelColor=333333&logo=codecov&logoColor=white)](https://codecov.io/gh/CogitatorTech/omni-nli)
[![Python Version](https://img.shields.io/badge/python-%3E=3.10-3776ab?style=flat&labelColor=333333&logo=python&logoColor=white)](https://github.com/CogitatorTech/omni-nli)
[![PyPI](https://img.shields.io/pypi/v/omni-nli?style=flat&labelColor=333333&logo=pypi&logoColor=white)](https://pypi.org/project/omni-nli/)
[![License](https://img.shields.io/badge/license-MIT-00acc1?style=flat&labelColor=333333&logo=open-source-initiative&logoColor=white)](https://github.com/CogitatorTech/omni-nli/blob/main/LICENSE)

A multi-interface (REST and MCP) server for natural language inference

</div>

---

Omni-NLI is a self-hostable server that provides natural language inference (NLI) capabilities via a REST API and the Model Context Protocol (MCP).
It can be used both as a very scalable standalone microservice and also as an MCP server for AI agents to implement a verification layer for AI-based
applications.

### What is NLI?

Given two pieces of text called premise (or fact) and hypothesis (or claim), NLI is the task of determining the relationship between them.
The relationship is typically shown by one of three labels:
- `"entailment"`: the hypothesis is supported or proved by the premise
- `"contradiction"`: the hypothesis is refuted or contradicts the premise
- `"neutral"`: the hypothesis is neither supported nor refuted by the premise

NLI is useful for a lot of applications, like fact-checking the output of large language models (LLMs) and checking the correctness of the answers a
question-answering system generates.

### Features

- Supports models provided by different backends, including Ollama, HuggingFace, or OpenRouter
- Supports REST API (for traditional applications) and MCP (for AI agent integration) interfaces
- Fully configurable and very scalable

See [ROADMAP.md](ROADMAP.md) for the list of implemented and planned features.

> [!IMPORTANT]
> Omni-NLI is in early development, so bugs and breaking changes are expected.
> Please use the [issues page](https://github.com/CogitatorTech/omni-nli/issues) to report bugs or request features.

---

### Quickstart

#### 1. Install the Server

```sh
pip install omni-nli
```

#### 2. Configure Backends

Copy the example config and add your API keys:

```sh
cp .env.example .env
# Edit .env to configure the model backends and other settings
```

#### 3. Start the Server

```sh
omni-nli
```

The server will be listening on `http://127.0.0.1:8000` by default.

#### 4. Evaluate NLI

```sh
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "premise": "A soccer player kicks a ball into the goal.",
    "hypothesis": "The soccer player is asleep on the field."
  }' \
  http://127.0.0.1:8000/api/v1/tools/evaluate_nli/invoke
```

Response:

```json
{
    "content": [
        {
            "type": "json",
            "data": {
                "label": "contradiction",
                "confidence": 1.0,
                "thinking_trace": null,
                "usage": {
                    "total_tokens": 188,
                    "thinking_tokens": 0,
                    "prompt_tokens": 172,
                    "completion_tokens": 16
                },
                "model": "Qwen/Qwen2.5-1.5B-Instruct",
                "backend": "huggingface"
            }
        }
    ]
}
```

---

### API Reference

#### REST API: `POST /api/v1/tools/evaluate_nli/invoke`

Request body schema:

```json
{
    "premise": "The base factual statement.",
    "hypothesis": "The statement to test against the premise.",
    "context": "An optional background context to prime the model.",
    "backend": "ollama",
    "model": "llama3.2",
    "use_reasoning": false
}
```

Parameters in the request body:

| Parameter       | Type    | Default  | Description                                                                     |
|-----------------|---------|----------|---------------------------------------------------------------------------------|
| `premise`       | string  | required | The base factual statement                                                      |
| `hypothesis`    | string  | required | The statement to test                                                           |
| `context`       | string  | null     | Optional background context to ground the inference                             |
| `backend`       | string  | null     | `"ollama"`, `"huggingface"`, or `"openrouter"`. Uses configured default if null |
| `model`         | string  | null     | Specific model to use. Uses backend default if null                             |
| `use_reasoning` | boolean | `false`  | Enable extended thinking (when supported by the model)                          |

Response:

| Field            | Type           | Description                                       |
|------------------|----------------|---------------------------------------------------|
| `label`          | string         | `"entailment"`, `"contradiction"`, or `"neutral"` |
| `confidence`     | float          | Confidence score (0.0 - 1.0)                      |
| `thinking_trace` | string or null | Reasoning trace if `use_reasoning` is enabled     |
| `model`          | string         | Model that was used                               |
| `backend`        | string         | Backend provider used                             |
| `usage`          | object         | Token usage statistics                            |

---

### MCP Integration

The server exposes its tools over MCP at `http://127.0.0.1:8000/mcp/`.

Claude Desktop / LM Studio Configuration:

```json
{
    "mcpServers": {
        "omni-nli": {
            "url": "http://127.0.0.1:8000/mcp/"
        }
    }
}
```

Available MCP Tools:

| Tool             | Description                                                               |
|------------------|---------------------------------------------------------------------------|
| `evaluate_nli`   | Analyzes premise/hypothesis pairs to determine their logical relationship |
| `list_providers` | Lists available backend providers and their configuration status          |

---

### Configuration

All settings can be configured via environment variables or CLI arguments.

See [.env.example](.env.example) for the complete list:

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

CLI Arguments:

```sh
omni-nli --host 0.0.0.0 --port 8080 --default-backend openrouter --default-model anthropic/claude-3.5-sonnet
```

---

### Supported Backends

| Backend     | Local | Reasoning Support | Example Models                                        |
|-------------|-------|-------------------|-------------------------------------------------------|
| Ollama      | Yes   | No                | `llama3.2`, `mistral`, `qwen2.5`                      |
| HuggingFace | Yes   | No                | `meta-llama/Llama-3.2-3B-Instruct`                    |
| OpenRouter  | No    | Yes               | `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-r1` |

---

### Documentation

The REST API includes interactive documentation available when running the server:

- **Swagger UI**: `/docs` (e.g., http://127.0.0.1:8000/docs)
- **ReDoc**: `/redoc` (e.g., http://127.0.0.1:8000/redoc)

These interfaces provide complete details on all available endpoints, parameters, and response schemas.

---

### Contributing

Contributions are always welcome!
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

### License

Omni-NLI is licensed under the MIT License (see [LICENSE](LICENSE)).

### Acknowledgements

- The logo is from [SVG Repo](https://www.svgrepo.com/svg/480613/puzzle-9) with some modifications.
