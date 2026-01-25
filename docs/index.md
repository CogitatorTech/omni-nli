# Omni-NLI

<div align="center">
  <picture>
    <img alt="Omni-NLI Logo" src="https://raw.githubusercontent.com/CogitatorTech/omni-nli/main/logo.svg" width="200">
  </picture>
</div>

Omni-NLI is a self-hostable server that provides Natural Language Inference (NLI) capabilities via a REST API and the Model Context Protocol (MCP).

It is designed to be a scalable standalone microservice or a tool layer for AI agents, allowing them to verify logical consistency and detect hallucinations.

## Key Features

- Multi-Backend Support: Use generic models through Ollama (local), HuggingFace (local transformers), or OpenRouter (cloud APIs).
- Dual Interface:
    - REST API: For traditional web/backend integration.
    - MCP Server: For direct integration with Claude Desktop, LM Studio, and other MCP clients.
- Advanced Logic:
    - Entailment/Contradiction Detection: Determine if a hypothesis follows from a premise.
    - Thinking Traces: Extract reasoning steps from models that support it.
    - Confidence Scores: Get numerical confidence for predictions.
- Production Ready:
    - Asynchronous I/O for high concurrency.
    - Caching for provider instances.
    - Standardized error handling and validation.

## Quick Links

- [Getting Started](getting-started.md): Installation and configuration guide.
- [Examples](examples.md): Usage examples for REST and MCP.
- [API Reference](api-reference.md): Detailed API documentation.
- [GitHub Repository](https://github.com/CogitatorTech/omni-nli): Source code and contributions.
