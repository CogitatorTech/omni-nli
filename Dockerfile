# File: Dockerfile
ARG BACKEND=cpu

# --- Builder Stage ---
FROM python:3.12-slim-trixie AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update -q && \
    apt-get install -qy --no-install-recommends build-essential git && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY ./src ./src
COPY ./scripts ./scripts
COPY Makefile ./

# Upgrade pip and install build tools
RUN pip install --upgrade pip build

# Build the wheel
RUN python -m build --wheel

# --- Common Final Base ---
FROM python:3.12-slim-trixie as common-final
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libsm6 libxext6 libxrender1 procps curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser && mkdir -p /home/appuser/app
WORKDIR /home/appuser/app

# Copy artifacts
COPY --from=builder /app/dist/*.whl .
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/pyproject.toml ./pyproject.toml

# Setup venv
RUN python -m venv /home/appuser/app/.venv && \
    /home/appuser/app/.venv/bin/pip install --upgrade pip

# --- CPU Target ---
FROM common-final AS cpu
# Install the wheel (and dependencies)
RUN /home/appuser/app/.venv/bin/pip install --no-cache-dir omni_nli-*.whl

USER appuser
ENTRYPOINT ["/bin/bash", "/home/appuser/app/scripts/docker_entrypoint.sh"]

# --- CUDA Target ---
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS cuda
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common wget && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3.12-dev \
    libglib2.0-0 libgl1 libsm6 libxext6 libxrender1 procps curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser && mkdir -p /home/appuser/app
WORKDIR /home/appuser/app

# Copy artifacts from builder
COPY --from=builder /app/dist/*.whl .
COPY --from=builder /app/scripts ./scripts

# Setup venv with Python 3.12
RUN python3.12 -m venv /home/appuser/app/.venv && \
    /home/appuser/app/.venv/bin/pip install --upgrade pip

# Install PyTorch with CUDA support first
RUN /home/appuser/app/.venv/bin/pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install the app
RUN /home/appuser/app/.venv/bin/pip install --no-cache-dir omni_nli-*.whl

USER appuser
ENTRYPOINT ["/bin/bash", "/home/appuser/app/scripts/docker_entrypoint.sh"]
