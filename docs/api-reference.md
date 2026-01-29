# API Reference

Omni-NLI includes interactive API documentation (via Swagger UI and ReDoc) for the REST API.
When the server is running, you can access them at:

  - Swagger UI: [http://127.0.0.1:8000/api/v1/apidoc/swagger](http://127.0.0.1:8000/api/v1/apidoc/swagger)
  - ReDoc: [http://127.0.0.1:8000/api/v1/apidoc/redoc](http://127.0.0.1:8000/api/v1/apidoc/redoc)

!!! important
    The REST API and MCP interface provide more or less the same functionality.
    The REST API can be more scalable because it is stateless compared to the MCP, which is a stateful service protocol.

## REST API

The REST API provides endpoints for NLI evaluation and provider management.
All endpoints are available under the `/api/v1` prefix.
A health check endpoint is also available at `GET /api/health`.

### POST `/api/v1/nli/evaluate`

Evaluates the logical relationship between a premise and a hypothesis.

Request body parameters:

| Parameter     | Type    | Default  | Description                                                               |
|:--------------|:--------|:---------|:--------------------------------------------------------------------------|
| premise       | string  | required | The base factual statement (premise)                                      |
| hypothesis    | string  | required | The statement to test against the premise (hypothesis)                    |
| context       | string  | null     | Optional background context to ground the inference                       |
| backend       | string  | null     | `ollama`, `huggingface`, or `openrouter`. Uses configured default if null |
| model         | string  | null     | Specific model to use. Uses the backend's default if null                 |
| use_reasoning | boolean | false    | Enable extended thinking                                                  |

Response fields:

| Field          | Type           | Description                                                                              |
|:---------------|:---------------|:-----------------------------------------------------------------------------------------|
| label          | string         | `entailment`, `contradiction`, or `neutral`                                              |
| confidence     | float          | Confidence score (between 0.0 to 1.0)                                                    |
| thinking_trace | string or null | Reasoning trace extracted from `<think>` tags or from pre-JSON text that model generates |
| model          | string         | Model that was used                                                                      |
| backend        | string         | Backend provider used                                                                    |

### GET `/api/v1/providers`

Returns provider configuration metadata.

Response includes:

- `ollama`, `huggingface`, and `openrouter`: Each provider object contains configuration details.
- `token_configured`: Indicates if credentials are available in the environment where the server is running.
- `default_model`: The default model for each provider.
- `default_backend`: The configured default backend.

## MCP Interface

The server exposes its capabilities as tools over the Model Context Protocol (MCP).
The MCP endpoint is available at http://127.0.0.1:8000/mcp/.

### Available Tools

| Tool           | Description                                                               |
|:---------------|:--------------------------------------------------------------------------|
| evaluate_nli   | Analyzes premise/hypothesis pairs to determine their logical relationship |
| list_providers | Lists available backend providers and their configuration status          |

The `evaluate_nli` tool accepts the same parameters as the REST endpoint.
The `list_providers` tool takes no arguments and returns the same information as the `GET /api/v1/providers` endpoint (including `default_backend`).
