## Implemented Features

This document outlines the features planned for the Omni-NLI project and their current implementation status.

> [!IMPORTANT]
> This roadmap is a work in progress and can change without notice.

### Core NLI Functionality

- [x] Natural language inference classification (entailment, contradiction, or neutral)
- [x] Confidence score estimation for predictions
- [x] Extended thinking/reasoning trace extraction
- [x] Configurable default backend and model
- [x] Per-request backend and model overrides
- [x] Context grounding support for logic verification

---

### Backend Providers

- [x] Ollama
- [x] HuggingFace (using the Transformers library)
- [x] OpenRouter

---

### Interfaces

- [x] REST API with OpenAPI documentation (Swagger UI and ReDoc)
- [x] MCP (Model Context Protocol) for AI agent integration
- [x] Streamable HTTP transport for MCP
- [x] Standardized JSON error responses
- [x] Pydantic validation for all inputs

---

### Performance

- [x] Asynchronous I/O for concurrent request handling
- [x] Provider instance caching (using LRU)
- [ ] Request rate limiting
- [ ] Response caching for identical queries

---

### Deployment

- [x] Standalone microservice architecture
- [x] Configuration via environment variables
- [x] CLI argument overrides
- [x] Docker support
- [x] Pre-built Docker images (CPU and CUDA)

---

### Development and Testing

- [x] Unit tests with pytest
- [x] Code coverage reporting
- [ ] Integration tests with live backends
- [ ] End-to-end API tests
- [ ] Performance benchmarks

---

### Documentation

- [x] README with a quickstart guide
- [x] Configuration reference (.env.example)
- [x] MkDocs documentation (API reference, getting started, and examples)
