# ==============================================================================
# VARIABLES
# ==============================================================================
PYTHON      ?= python3
PIP         ?= pip3
DEP_MNGR    ?= uv
DOCS_DIR    ?= docs
DOCKERFILE   ?= Dockerfile
GUNICORN_NUM_WORKERS ?= 4

# Server configuration (can be overridden by environment variables)
PORT      ?= 8000
HOST      ?= 0.0.0.0

# Directories and files to clean
CACHE_DIRS  = .mypy_cache .pytest_cache .ruff_cache
COVERAGE    = .coverage htmlcov coverage.xml
DIST_DIRS   = dist junit
TMP_DIRS    = site

.DEFAULT_GOAL := help

# ==============================================================================
# HELP
# ==============================================================================
.PHONY: help
help: ## Show the help messages for all targets
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' Makefile | \
	awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# SETUP & INSTALLATION
# ==============================================================================
.PHONY: setup
setup: ## Install system dependencies and dependency manager (e.g., Poetry)
	sudo apt-get update
	sudo apt-get install -y python3-pip docker.io
	$(PIP) install --upgrade pip
	$(PIP) install $(DEP_MNGR)

.PHONY: install
install: ## Install Python dependencies
	$(DEP_MNGR) sync --all-extras

# ==============================================================================
# QUALITY & TESTING
# ==============================================================================
.PHONY: test
test: ## Run tests
	$(DEP_MNGR) run pytest

.PHONY: lint
lint: ## Run linter checks
	$(DEP_MNGR) run ruff check --fix

.PHONY: format
format: ## Format code
	$(DEP_MNGR) run ruff format

.PHONY: typecheck
typecheck: ## Typecheck code
	$(DEP_MNGR) run mypy .

.PHONY: setup-hooks
setup-hooks: ## Install Git hooks (pre-commit and pre-push)
	$(DEP_MNGR) run pre-commit install --hook-type pre-commit
	$(DEP_MNGR) run pre-commit install --hook-type pre-push
	$(DEP_MNGR) run pre-commit install-hooks

.PHONY: test-hooks
test-hooks: ## Test Git hooks on all files
	$(DEP_MNGR) run pre-commit run --all-files

# ==============================================================================
# APPLICATION
# ==============================================================================
.PHONY: run
run: ## Start the server
	@echo "Starting the server..."
	$(DEP_MNGR) run omni-nli --host $(HOST) --port $(PORT) --log-level DEBUG

.PHONY: run-gunicorn
run-gunicorn: ## Start the server with Gunicorn
	@echo "Starting the Omni-NLI server with Gunicorn..."
	$(DEP_MNGR) run gunicorn -w $(GUNICORN_NUM_WORKERS) -k uvicorn.workers.UvicornWorker omni_nli:starlette_app

# ==============================================================================
# BUILD & PUBLISH
# ==============================================================================
.PHONY: build
build: ## Build distributions
	$(DEP_MNGR) build

.PHONY: publish
publish: build ## Publish to PyPI (requires PYPI_TOKEN)
	@$(DEP_MNGR) publish --token $(PYPI_TOKEN)

# ==============================================================================
# EXAMPLES
# ==============================================================================
.PHONY: example-rest example-mcp

SERVER_PID := /tmp/omni-nli-server.pid

# Define the lists of example files
REST_EXAMPLES := $(wildcard examples/rest/*.py)
MCP_EXAMPLES := $(wildcard examples/mcp/*.py)

define run_examples
	@echo "Starting server in background..."
	$(DEP_MNGR) run omni-nli > /dev/null 2>&1 & echo $$! > $(SERVER_PID)
	@echo "Waiting for server to start..."
	@while ! nc -z 127.0.0.1 8000; do sleep 1; done
	@echo "Server started. Running $(1) examples..."
	@for example in $(2); do \
		echo "\n--- Running $$example ---"; \
		$(DEP_MNGR) run python $$example; \
	done
	@echo "\nStopping server..."
	@kill `cat $(SERVER_PID)`
endef

example-rest: ## Run all REST API examples
	$(call run_examples,"REST",$(REST_EXAMPLES))

example-mcp: ## Run all MCP API examples
	$(call run_examples,"MCP",$(MCP_EXAMPLES))

# ==============================================================================
# DOCKER
# ==============================================================================
IMAGE_NAME ?= omni-nli

.PHONY: docker-build
docker-build: ## Build the Docker image
	docker build -t $(IMAGE_NAME):latest -f Dockerfile .

.PHONY: docker-run
docker-run: ## Run the Docker container
	docker run --rm -it -p $(PORT):$(PORT) $(IMAGE_NAME):latest

# ==============================================================================
# MAINTENANCE
# ==============================================================================
.PHONY: clean
clean: ## Remove caches and build artifacts
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf $(CACHE_DIRS) $(COVERAGE) $(DIST_DIRS) $(TMP_DIRS)

.PHONY: docker-prune
docker-prune: ## Remove dangling (untagged) Docker images
	@echo "Removing dangling Docker images..."
	docker image prune -f

# ==============================================================================
# DOCUMENTATION
# ==============================================================================
.PHONY: docs
docs: ## Generate documentation using MkDocs
	@echo "Generating MkDocs documentation..."
	@$(DEP_MNGR) run mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "Serving MkDocs documentation locally..."
	@$(DEP_MNGR) run mkdocs serve --dev-addr localhost:8001
