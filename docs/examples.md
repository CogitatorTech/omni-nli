# Examples

## REST API

You can interact with Omni-NLI using standard HTTP requests.

### Basic Evaluation

Request:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/nli/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "premise": "A football player kicks a ball into the goal.",
    "hypothesis": "The football player is asleep on the field."
  }'
```

Response:

```json
{
    "label": "contradiction",
    "confidence": 0.99,
    "model": "qwen3:8b",
    "backend": "ollama"
}
```

### Using Context and Reasoning

You can provide context and enable extended thinking for more detailed reasoning traces.

```sh
curl -X POST http://127.0.0.1:8000/api/v1/nli/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "premise": "The user has clicked the delete button.",
    "hypothesis": "The file is permanently removed.",
    "context": "The system implements a soft-delete mechanism where files are moved to a trash bin first.",
    "use_reasoning": true,
    "backend": "openrouter",
    "model": "google/gemini-2.5-flash"
  }'
```

Example response:

```json
{
  "label": "contradiction",
  "confidence": 1.0,
  "thinking_trace": "The user clicked the delete button. The system has a soft-delete mechanism where files are moved to a trash bin first. This means that clicking delete does *not* permanently remove the file; it moves it to the trash. Therefore, the hypothesis that the file is permanently removed contradicts the premise in the context of the system's behavior.",
  "model": "google/gemini-2.5-flash",
  "backend": "openrouter"
}
```


!!! note
    The `thinking_trace` field is only returned when `use_reasoning` is enabled and the server is configured with `RETURN_THINKING_TRACE=True`.
    Reasoning is extracted from models that output it via `<think></think>` tags (like DeepSeek-R1, Qwen models, etc.) or from any text the comes before the JSON response from the model.

!!! important
    Not all models support reasoning.

### Listing Providers

```sh
curl http://127.0.0.1:8000/api/v1/providers
```

Response:

```json
{
    "ollama": 
    {
        "host": "http://localhost:11434",
        "default_model": "qwen3:8b"
    },
    "huggingface": 
    {
        "token_configured": false,
        "default_model": "microsoft/Phi-3.5-mini-instruct"
    },
    "openrouter": 
    {
        "token_configured": true,
        "default_model": "openai/gpt-5-mini"
    },
    "default_backend": "huggingface"
}
```

## MCP Server

Omni-NLI allows AI agents and applications that can use MCP (for example, [Claude Code](https://claude.com/product/claude-code)
or [LM Studio](https://lmstudio.ai/)) to use NLI as a tool.

### MCP Client Configuration

Add the following to your MCP client config file:

```json
{
    "mcpServers": {
        "omni-nli": {
            "url": "http://127.0.0.1:8000/mcp/"
        }
    }
}
```
