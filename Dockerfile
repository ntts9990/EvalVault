# EvalVault Dockerfile
# Multi-stage build for optimized production image

# Stage 0: uv binary
ARG PYTHON_IMAGE=python:3.12.6-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.4.28
FROM ${UV_IMAGE} AS uv

# Stage 1: Build stage
FROM ${PYTHON_IMAGE} AS builder

# Install uv
COPY --from=uv /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Install the project
RUN uv sync --frozen --no-dev


# Stage 2: Runtime stage
ARG PYTHON_IMAGE=python:3.12.6-slim
FROM ${PYTHON_IMAGE} AS runtime

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash evalvault

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code (needed for editable install)
COPY --from=builder /app/src /app/src

# Copy config files
COPY --from=builder /app/config /app/config

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R evalvault:evalvault /app

# Switch to non-root user
USER evalvault

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD evalvault --help || exit 1

# Default command
ENTRYPOINT ["evalvault"]
CMD ["--help"]
