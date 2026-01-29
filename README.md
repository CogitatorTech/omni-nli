<div align="center">
  <picture>
    <img alt="Omni-NLI Logo" src="logo.svg" width="200">
  </picture>
<br>

<h2>Omni-NLI</h2>

[![Tests](https://img.shields.io/github/actions/workflow/status/CogitatorTech/omni-nli/tests.yml?label=tests&style=flat&labelColor=333333&logo=github&logoColor=white)](https://github.com/CogitatorTech/omni-nli/actions/workflows/tests.yml)
[![Code Coverage](https://img.shields.io/codecov/c/github/CogitatorTech/omni-nli?style=flat&label=coverage&labelColor=333333&logo=codecov&logoColor=white)](https://codecov.io/gh/CogitatorTech/omni-nli)
[![Python Version](https://img.shields.io/badge/python-%3E=3.10-3776ab?style=flat&labelColor=333333&logo=python&logoColor=white)](https://github.com/CogitatorTech/omni-nli)
[![PyPI](https://img.shields.io/pypi/v/omni-nli?style=flat&labelColor=333333&logo=pypi&logoColor=white)](https://pypi.org/project/omni-nli/)
[![Documentation](https://img.shields.io/badge/docs-read-00acc1?style=flat&labelColor=282c34&logo=readthedocs)](https://CogitatorTech.github.io/omni-nli/)
[![License](https://img.shields.io/badge/license-MIT-00acc1?style=flat&labelColor=333333&logo=open-source-initiative&logoColor=white)](https://github.com/CogitatorTech/omni-nli/blob/main/LICENSE)
<br>
[![Examples](https://img.shields.io/badge/examples-view-green?style=flat&labelColor=382c34)](https://github.com/CogitatorTech/omni-nli/tree/main/examples)
[![Docker Image (CPU)](https://img.shields.io/badge/Docker-CPU-007ec6?style=flat&logo=docker)](https://github.com/CogitatorTech/omni-nli/pkgs/container/omni-nli-cpu)
[![Docker Image (CUDA)](https://img.shields.io/badge/Docker-CUDA-007ec6?style=flat&logo=docker)](https://github.com/CogitatorTech/omni-nli/pkgs/container/omni-nli-cuda)

A multi-interface (REST and MCP) server for natural language inference

</div>

---

Omni-NLI is a self-hostable server that provides [natural language inference (NLI)](https://en.wikipedia.org/wiki/Textual_entailment) capabilities via
RESTful and the Model Context Protocol (MCP) interfaces.
It can be used both as a very scalable standalone stateless microservice and also as an MCP server for AI agents to implement a verification layer
for AI-based applications like chatbots or virtual assistants.

### What is NLI?

Given two pieces of text called premise and hypothesis, NLI is the task of determining the logical relationship between them if it was done by a human.
The relationship is typically shown by one of three labels:

- `"entailment"`: the hypothesis is supported by the premise
- `"contradiction"`: the hypothesis is contradicted by the premise
- `"neutral"`: the hypothesis is neither supported nor contradicted by the premise

NLI is useful for a lot of applications, like fact-checking the output of large language models (LLMs) and checking the correctness of the answers a
question-answering system generates.

### Main Features

- Supports models provided by different backends, including Ollama, HuggingFace (public and private/gated models), and OpenRouter
- Supports REST API (for traditional applications) and MCP (for AI agents) interfaces
- Fully configurable and very scalable, with built-in caching
- Provides confidence scores and (optional) reasoning traces for explainability

Below is the high-level architecture of Omni-NLI:

![Architecture Diagram](docs/assets/diagrams/architecture.svg)

See [ROADMAP.md](ROADMAP.md) for the list of implemented and planned features.

> [!IMPORTANT]
> Omni-NLI is in early development, so bugs and breaking changes are expected.
> Please use the [issues page](https://github.com/CogitatorTech/omni-nli/issues) to report bugs or request features.

---

### Quickstart

#### 1. Installation

```sh
pip install omni-nli
```

#### 2. Start the Server

```sh
omni-nli
```

#### 3. Evaluate NLI

```sh
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "premise": "A football player kicks a ball into the goal.",
    "hypothesis": "The football player is asleep on the field."
  }' \
  http://127.0.0.1:8000/api/v1/nli/evaluate
```

Example response:

```json
{
    "label": "contradiction",
    "confidence": 0.99,
    "model": "microsoft/Phi-3.5-mini-instruct",
    "backend": "huggingface"
}
```

---

### Documentation

Check out the [Omni-NLI Documentation](https://cogitatortech.github.io/omni-nli/) for more information, including configuration options, API
reference, and examples.

---

### Contributing

Contributions are always welcome!
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

### License

Omni-NLI is licensed under the MIT License (see [LICENSE](LICENSE)).

### Acknowledgements

- The logo is from [SVG Repo](https://www.svgrepo.com/svg/480613/puzzle-9) with some modifications.


<!-- Need to add this line for MCP registry publication -->
<!-- mcp-name: io.github.CogitatorTech/omni-nli -->
