# Examples

## REST API

You can interact with Omni-NLI using standard HTTP requests.

### Basic Evaluation

Request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tools/evaluate_nli/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "premise": "A soccer player kicks a ball into the goal.",
    "hypothesis": "The soccer player is asleep on the field."
  }'
```

Response:

```json
{
  "content": [
    {
      "type": "json",
      "data": {
        "label": "contradiction",
        "confidence": 0.99,
        "thinking_trace": null,
        "usage": {
          "total_tokens": 150,
          "prompt_tokens": 120,
          "completion_tokens": 30
        },
        "model": "llama3.2",
        "backend": "ollama"
      }
    }
  ]
}
```

### Using Context and Reasoning

You can provide context and request "reasoning" (if the model supports it, e.g., deepseek-r1).

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tools/evaluate_nli/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "premise": "The user has clicked the delete button.",
    "hypothesis": "The file is permanently removed.",
    "context": "The system implements a soft-delete mechanism where files are moved to a trash bin first.",
    "use_reasoning": true,
    "backend": "openrouter",
    "model": "deepseek/deepseek-r1"
  }'
```

---

## MCP (Model Context Protocol)

Omni-NLI allows AI agents (like Claude Desktop) to use NLI as a tool.

### Claude Desktop Configuration

Add the following to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "omni-nli": {
      "url": "http://127.0.0.1:8000/mcp/"
    }
  }
}
```

### Usage in Chat

Once connected, you can ask Claude to verify statements:

> "User: Verify if the following claim contradicts the provided text..."
>
> Claude: Calls evaluate_nli tool...
