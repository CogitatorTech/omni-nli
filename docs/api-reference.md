# API Reference

## Interactive Documentation

When the server is running, interactive documentation is available at:

- Swagger UI: /api/v1/docs (http://127.0.0.1:8000/api/v1/docs)
- ReDoc: /api/v1/redoc (http://127.0.0.1:8000/api/v1/redoc)

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
| model         | string  | null     | Specific model to use. Uses backend default if null                 |
| use_reasoning | boolean | false    | Enable extended thinking (only for reasoning-capable backends)      |

Response Fields:

| Field          | Type           | Description                                 |
|:---------------|:---------------|:--------------------------------------------|
| label          | string         | entailment, contradiction, or neutral       |
| confidence     | float          | Confidence score (0.0 - 1.0)                |
| thinking_trace | string \| null | Reasoning trace if use_reasoning is enabled |
| model          | string         | Model that was used                         |
| backend        | string         | Backend provider used                       |
| usage          | object         | Token usage statistics                      |

### GET /api/v1/providers

Returns provider status and configuration metadata.

### GET /api/v1/models?backend=ollama|huggingface|openrouter

Lists models available for a backend.

## MCP Integration

The server exposes its tools over MCP at http://127.0.0.1:8000/mcp/.

Available MCP Tools:

| Tool           | Description                                                               |
|:---------------|:--------------------------------------------------------------------------|
| evaluate_nli   | Analyzes premise/hypothesis pairs to determine their logical relationship |
| list_providers | Lists available backend providers and their configuration status          |
