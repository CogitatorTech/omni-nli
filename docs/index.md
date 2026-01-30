# Omni-NLI

<div align="center">
  <picture>
    <img alt="Omni-NLI Logo" src="https://raw.githubusercontent.com/CogitatorTech/omni-nli/main/logo.svg" width="200">
  </picture>
</div>

Omni-NLI is a self-hostable server that provides [natural language inference (NLI)](https://en.wikipedia.org/wiki/Textual_entailment) capabilities via
RESTful and the Model Context Protocol (MCP) interfaces.
It can be used both as a very scalable standalone stateless microservice and also as an MCP server for AI agents to implement a verification layer
for AI-based applications.

![Architecture Diagram](https://raw.githubusercontent.com/CogitatorTech/omni-nli/main/docs/assets/diagrams/architecture.svg)

## What is NLI?

Given two pieces of text called premise and hypothesis, NLI (AKA textual entailment) is the task of determining the directional relationship between
them as it is perceived by a human reader.
The relationship is given one of these three labels:

- `"entailment"`: the hypothesis is supported by the premise
- `"contradiction"`: the hypothesis is contradicted by the premise
- `"neutral"`: the hypothesis is neither supported nor contradicted by the premise

!!! note
    NLI is not the same as logical entailment.
    Its goal is to determine if a reasonable human would consider the hypothesis to follow from the premise.
    This checks for consistency instead of the absolute truth of the hypothesis.

Typical applications of NLI include:

* NLI can be used to check if a given piece of text is consistent with the rest of the text. For example, if a new response
  from a chatbot or AI assistant contradicts something that was said earlier in the conversation.
* It can be used to check if a summarization contradicts the original text in some way.
* It can be used to check if the documents in the ranked list of results entail the query.
* It can be used to check if a piece of text is supported by some facts. Note that this is not the same as using logic.

!!! note
    The quality of the results depends a lot on the model (the LLM) that is used.
    A good strategy is to first fine-tune the model using a dataset of premise-hypothesis-label triples that are relevant to your application domain.

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

## Quick Links

- [Getting Started](getting-started.md): Installation and configuration guide.
- [Examples](examples.md): Usage examples for REST and MCP interfaces.
- [API Reference](api-reference.md): Detailed API documentation.
