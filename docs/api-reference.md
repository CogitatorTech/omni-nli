# API Reference

## Interactive Documentation

When the server is running, detailed interactive documentation is available at:

- Swagger UI: /docs (e.g., [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs))
- ReDoc: /redoc (e.g., [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc))

## Endpoints

### POST /api/v1/tools/evaluate_nli/invoke

Evaluates the logical relationship between a premise and a hypothesis.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| premise | string | Yes | The factual statement to rely on. |
| hypothesis | string | Yes | The claim to be verified against the premise. |
| context | string | No | Additional background context. |
| backend | string | No | ollama, huggingface, or openrouter. |
| model | string | No | Specific model identifier (e.g., llama3.2). |
| use_reasoning | boolean | No | Request reasoning trace (default: false). |

Response Schema:

The response follows the MCP tool call result format.

```json
{
  "content": [
    {
      "type": "json",
      "data": {
        "label": "entailment | contradiction | neutral",
        "confidence": 0.0-1.0,
        "thinking_trace": "string (optional)",
        "model": "string",
        "backend": "string"
      }
    }
  ]
}
```

## MCP Tools

The server exposes the following tools via MCP:

### evaluate_nli
Same functionality as the REST endpoint described above.

### list_providers
Lists the currently configured backend providers and their status.
