# API Reference

## Interactive Documentation

When the server is running, detailed interactive documentation is available at:

- Swagger UI: /docs ([http://127.0.0.1:8000/api/v1/apidoc/swagger](http://127.0.0.1:8000/api/v1/apidoc/swagger))
- ReDoc: /redoc ([http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc))

## Endpoints

### POST /api/v1/tools/evaluate_nli/invoke

Evaluates the logical relationship between a premise and a hypothesis.

Request Body Parameters:

| Parameter     | Type    | Default  | Description                                                         |
|:--------------|:--------|:---------|:--------------------------------------------------------------------|
| premise       | string  | required | The base factual statement                                          |
| hypothesis    | string  | required | The statement to test against the premise                           |
| context       | string  | null     | Optional background context to ground the inference                 |
| backend       | string  | null     | ollama, huggingface, or openrouter. Uses configured default if null |
| model         | string  | null     | Specific model to use. Uses backend default if null                 |
| use_reasoning | boolean | false    | Enable extended thinking (when supported by the model)              |

Response Fields:

| Field          | Type           | Description                                 |
|:---------------|:---------------|:--------------------------------------------|
| label          | string         | entailment, contradiction, or neutral       |
| confidence     | float          | Confidence score (0.0 - 1.0)                |
| thinking_trace | string \| null | Reasoning trace if use_reasoning is enabled |
| model          | string         | Model that was used                         |
| backend        | string         | Backend provider used                       |
| usage          | object         | Token usage statistics                      |

## MCP Integration

The server exposes its tools over MCP at http://127.0.0.1:8000/mcp/.

Available MCP Tools:

| Tool           | Description                                                               |
|:---------------|:--------------------------------------------------------------------------|
| evaluate_nli   | Analyzes premise/hypothesis pairs to determine their logical relationship |
| list_providers | Lists available backend providers and their configuration status          |
