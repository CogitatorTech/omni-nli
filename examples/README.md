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

2. **List Providers**
   ```bash
   python examples/rest/list_providers_example.py
   ```

3. **Health Check**
   ```bash
   python examples/rest/health_check_example.py
   ```

#### MCP Examples

1. **Evaluate NLI**
   ```bash
   python examples/mcp/evaluate_nli_example.py \
       --url "http://127.0.0.1:8000/mcp/" \
       --premise "It is raining." --hypothesis "The ground is wet." \
       --backend huggingface
   ```

### Options

Most examples accept the following arguments:

- `--url`: The endpoint URL (default depends on the example).
- `--premise`: The premise text.
- `--hypothesis`: The hypothesis text.
- `--backend`: The backend to use (`ollama`, `huggingface`, and `openrouter`).
- `--model`: Specific model name (optional).
