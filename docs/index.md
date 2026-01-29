# Omni-NLI

<div align="center">
  <picture>
    <img alt="Omni-NLI Logo" src="https://raw.githubusercontent.com/CogitatorTech/omni-nli/main/logo.svg" width="200">
  </picture>
</div>

Omni-NLI is a self-hostable server that provides [natural language inference (NLI)](https://en.wikipedia.org/wiki/Textual_entailment) capabilities via
RESTful and the Model Context Protocol (MCP) interfaces.
It can be used both as a very scalable standalone stateless microservice and also as an MCP server for AI agents to implement a verification layer
for AI-based applications like chatbots or virtual assistants.

## What is NLI?

Given two pieces of text called premise and hypothesis, NLI is the task of determining the logical relationship between them if it was done by a human.
The relationship is typically shown by one of three labels:

- `"entailment"`: the hypothesis is supported by the premise
- `"contradiction"`: the hypothesis is contradicted by the premise
- `"neutral"`: the hypothesis is neither supported nor contradicted by the premise

NLI is useful for a lot of applications, like fact-checking the output of large language models (LLMs) and checking the correctness of the answers a
question-answering system generates.

## High-level Features

- Multi-backend support: Use models through Ollama, HuggingFace (public and private/gated models), or OpenRouter.
- Dual interface:
    - REST API for conventional integration with other applications.
    - MCP Server for direct integration with AI agents.
- NLI capabilities:
    - Entailment and contradiction detection: Determine if a hypothesis follows from a premise given a model.
    - Thinking traces: Extract reasoning steps from models for explainability.
    - Confidence scores: Get numerical confidence for predictions.
- Scalable architecture:
    - Asynchronous I/O for high throughput.
    - Built-in caching.

Below is the high-level architecture of Omni-NLI:

![Architecture Diagram](https://raw.githubusercontent.com/CogitatorTech/omni-nli/main/docs/assets/diagrams/architecture.svg)

## Quick Links

- [Getting Started](getting-started.md): Installation and configuration guide.
- [Examples](examples.md): Usage examples for REST and MCP interfaces.
- [API Reference](api-reference.md): Detailed API documentation.
