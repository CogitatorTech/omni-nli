# Getting Started

This document includes installation and configuration instructions for Omni-NLI.
For a quickstart, please see the project's main [README.md](https://github.com/CogitatorTech/omni-nli/blob/main/README.md) file.

## Installation

You can run Omni-NLI either by installing it as a Python library or by using a pre-built Docker image.

### Python Installation

You can install Omni-NLI via pip:

```sh
pip install omni-nli
```

### Docker Installation

Pre-built Docker images are available from the [GitHub Container Registry](https://github.com/CogitatorTech/omni-nli/packages).

Generic CPU Image:

```sh
docker run --rm -it -p 8000:8000 ghcr.io/cogitatortech/omni-nli-cpu:latest
```

GPU Image (CUDA; for NVIDIA GPUs):

```sh
docker run --rm -it --gpus all -p 8000:8000 ghcr.io/cogitatortech/omni-nli-cuda:latest
```

Configuration can be passed as environment variables to the container.
For example, to use OpenRouter with a custom model:

```sh
docker run --rm -it -p 8000:8000 \
  -e DEFAULT_BACKEND=openrouter \
  -e OPENROUTER_API_KEY=your-api-key \
  -e OPENROUTER_DEFAULT_MODEL=openai/gpt-5.2 \
  ghcr.io/cogitatortech/omni-nli-cpu:latest
```

!!! tip
    When using the HuggingFace backend, the GPU image is recommended because inference will be a lot faster when using a GPU.

!!! warning
    When using the Ollama backend with Docker, you must set `OLLAMA_HOST` to point to a valid IP or host name that has Ollama server running on it. The default `localhost` will point to the container itself and will fail to connect.

!!! note
    The `latest` tag refers to the latest release on top of the `main` branch. You can replace `latest` with a specific version tag from
    the [list of available packages](https://github.com/CogitatorTech/omni-nli/packages).

## Configuration

The server can be configured using command-line arguments or environment variables.
Environment variables are read from a `.env` file if it exists or from the system environment.

!!! note
    Command-line arguments take precedence over environment variables.

You could copy the example [.env.example](https://github.com/CogitatorTech/omni-nli/blob/main/.env.example) in the project's repository to the directory where you run the server and customize it.

```sh
cp .env.example .env
```

### Configuration Reference

| Argument                      | Env Var                     | Description                              | Default                           |
|:------------------------------|:----------------------------|:-----------------------------------------|:----------------------------------|
| `--host`                      | `HOST`                      | Server host                              | `127.0.0.1`                       |
| `--port`                      | `PORT`                      | Server port                              | `8000`                            |
| `--log-level`                 | `LOG_LEVEL`                 | Logging level                            | `INFO`                            |
| `--debug`                     | `DEBUG`                     | Enable debug mode                        | `False`                           |
| `--default-backend`           | `DEFAULT_BACKEND`           | Default backend provider                 | `huggingface`                     |
| `--ollama-host`               | `OLLAMA_HOST`               | Ollama server URL                        | `http://localhost:11434`          |
| `--ollama-default-model`      | `OLLAMA_DEFAULT_MODEL`      | Default Ollama model                     | `qwen3:8b`                        |
| `--huggingface-default-model` | `HUGGINGFACE_DEFAULT_MODEL` | Default HuggingFace model                | `microsoft/Phi-3.5-mini-instruct` |
| `--openrouter-default-model`  | `OPENROUTER_DEFAULT_MODEL`  | Default OpenRouter model                 | `openai/gpt-5-mini`               |
| `--huggingface-token`         | `HUGGINGFACE_TOKEN`         | HuggingFace API token (for gated models) | `None`                            |
| `--openrouter-api-key`        | `OPENROUTER_API_KEY`        | OpenRouter API key                       | `None`                            |
| `--hf-cache-dir`              | `HF_CACHE_DIR`              | HuggingFace models cache directory       | OS default                        |
| `--max-thinking-tokens`       | `MAX_THINKING_TOKENS`       | Max tokens for thinking traces           | `4096`                            |
| `--return-thinking-trace`     | `RETURN_THINKING_TRACE`     | Return raw thinking trace in response    | `False`                           |

!!! note
    The `PROVIDER_CACHE_SIZE` setting must be configured via environment variable only, not CLI flag.

### Supported Backends

| Backend     | Local | Example Models                                                         |
|:------------|:------|:-----------------------------------------------------------------------|
| Ollama      | Yes   | `qwen3:8b`, `deepseek-r1:7b`, `phi4:latest`                                  |
| HuggingFace | Yes   | `microsoft/Phi-3.5-mini-instruct`, `Qwen/Qwen2.5-1.5B-Instruct`            |
| OpenRouter  | No    | `openai/gpt-5-mini`, `openai/gpt-5.2`, `arcee-ai/trinity-large-preview:free` |

## Running the Server

Start the server using the CLI command:

```sh
omni-nli
```

The server will start at http://127.0.0.1:8000 by default.

CLI arguments example:

```sh
omni-nli \
  --host 0.0.0.0 \
  --port 8080 \
  --default-backend openrouter \
  --openrouter-default-model openai/gpt-5.2
```
