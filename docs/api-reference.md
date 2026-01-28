# API Reference

## Interactive Documentation

This project provides interactive API documentation (Swagger UI and ReDoc). Once the server is running, you can access them at:

    Swagger UI: http://127.0.0.1:8000/api/v1/apidoc/swagger
    ReDoc: http://127.0.0.1:8000/api/v1/apidoc/redoc

## Endpoints

### POST /api/v1/nli/evaluate

Evaluates the logical relationship between a premise and a hypothesis.

Request Body Parameters:

| Parameter     | Type    | Default  | Description                                                         |
|:--------------|:--------|:---------|:--------------------------------------------------------------------|
| premise       | string  | required | The base factual statement (premise)                                |
| hypothesis    | string  | required | The statement to test against the premise (hypothesis)              |
| context       | string  | null     | Optional background context to ground the inference                 |
| backend       | string  | null     | ollama, huggingface, or openrouter. Uses configured default if null |
| model         | string  | null     | Specific model to use. Uses the backend's default if null           |
| use_reasoning | boolean | false    | Enable extended thinking                                            |

Response Fields:

| Field          | Type           | Description                                 |
|:---------------|:---------------|:--------------------------------------------|
| label          | string         | entailment, contradiction, or neutral       |
| confidence     | float          | Confidence score (between 0.0 to 1.0)       |
| thinking_trace | string \| null | Reasoning trace if use_reasoning is enabled |
| model          | string         | Model that was used                         |
| backend        | string         | Backend provider used                       |

### GET /api/v1/providers

Returns provider configuration metadata.

Notes:

- `token_configured` is **true** when credentials are present in the environment:
  - HuggingFace: `HUGGINGFACE_TOKEN` is set (needed for gated/private models)
  - OpenRouter: `OPENROUTER_API_KEY` is set
- Each provider always includes a `default_model` (there is no global default model).

## MCP Integration

The server exposes its tools over MCP at http://127.0.0.1:8000/mcp/.

Available MCP Tools:

| Tool           | Description                                                               |
|:---------------|:--------------------------------------------------------------------------|
| evaluate_nli   | Analyzes premise/hypothesis pairs to determine their logical relationship |
| list_providers | Lists available backend providers and their configuration status          |
