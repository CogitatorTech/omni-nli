## Omni-NLI Examples

This directory contains examples of how to use the Omni-NLI server via the REST and MCP interfaces.

### Prerequisites

Before running the examples, make sure the Omni-NLI server is running.

```bash
omni-nli
```

### Running the Examples

The example scripts are designed to be run from the root of the repository.

#### REST API Examples

1. **Evaluate NLI**
   ```bash
   python examples/rest/evaluate_nli_example.py \
       --premise "Cats are mammals." --hypothesis "Cats are animals." \
       --backend ollama
   ```

   Example output:
    ```json
    {
    "label": "entailment",
    "confidence": 1.0,
    "model": "qwen3:8b",
    "backend": "ollama"
   }
    ```

2. **List Providers**
   ```bash
   python examples/rest/list_providers_example.py
   ```

   Example output:
    ```json
    {
    "ollama": {
         "host": "http://localhost:11434",
         "token_configured": null,
         "cache_dir": null,
         "default_model": "qwen3:8b"
     },
    "huggingface": {
         "host": null,
         "token_configured": true,
         "cache_dir": "/home/hassan/.cache/huggingface/hub",
         "default_model": "microsoft/Phi-3.5-mini-instruct"
    },
    "openrouter": {
         "host": null,
         "token_configured": true,
         "cache_dir": null,
         "default_model": "openai/gpt-5-mini"
    },
         "default_backend": "huggingface"
    }
     ```

3. **Health Check**
   ```bash
   python examples/rest/health_check_example.py
   ```

   Example output:
    ```json
    {
    "status": "ok",
    "version": "0.1.0a3"
    }
    ```

#### MCP Examples

1. **Evaluate NLI (HuggingFace)**
   ```bash
   python examples/mcp/evaluate_nli_example.py \
       --url "http://127.0.0.1:8000/mcp/" \
       --premise "It is raining." --hypothesis "The ground is wet." \
       --backend huggingface
   ```

   Example output:
    ```json
    {
    "label":"entailment",
    "confidence":0.9,
    "model":"microsoft/Phi-3.5-mini-instruct",
    "backend":"huggingface"
   }
    ```
2. **Evaluate NLI (OpenRouter)**
   ```bash
   python examples/mcp/evaluate_nli_example.py \
       --url "http://127.0.0.1:8000/mcp/" \
       --premise "It is raining." --hypothesis "The ground is wet." \
       --backend openrouter \
       --model openai/gpt-5.2
   ```

   Example output:
    ```json
    {
    "label": "entailment",
    "confidence": 0.9,
    "model": "openai/gpt-5.2",
    "backend": "openrouter"
    }
    ```

### Options

Most examples accept the following arguments:

- `--url`: The endpoint URL (default depends on the example).
- `--premise`: The premise text.
- `--hypothesis`: The hypothesis text.
- `--backend`: The backend to use (`ollama`, `huggingface`, and `openrouter`).
- `--model`: Specific model name (optional).
