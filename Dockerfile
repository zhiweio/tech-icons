# ---------------------------------------------------------------------------
# tech-icons — MCP Server + Web UI Docker image
#
# Build:
#   docker build -t tech-icons .
#
# Run (MCP mode, default):
#   docker run -p 8765:8765 tech-icons
#
# Run (Web UI mode):
#   docker run -p 8765:8765 -e SERVER_MODE=web tech-icons
# ---------------------------------------------------------------------------

# ---- Stage 1: Build -------------------------------------------------------
FROM python:3.11-slim AS builder

# Use a consistent venv path so script shebangs remain valid across stages
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install uv for fast, reproducible package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build

# Install system deps needed for sentence-transformers (optional semantic search)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definitions AND package source before uv sync
# (uv sync needs the package dir to install the project itself into the venv)
COPY pyproject.toml uv.lock* ./
COPY tech_icons/ ./tech_icons/

# Install ALL deps + the project itself into /opt/venv (editable install not needed;
# uv sync builds the package from the local source tree)
RUN uv sync --frozen --no-dev --no-editable --extra web --extra semantic

# Copy remaining project files (README, docs, etc. — not strictly needed at runtime)
COPY . .

# ---- Stage 2: Runtime ------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="tech-icons"
LABEL org.opencontainers.image.description="MCP server for 3100+ cloud tech icons with Streamable HTTP transport"
LABEL org.opencontainers.image.url="https://github.com/zhiweio/tech-icons"
LABEL org.opencontainers.image.documentation="https://github.com/zhiweio/tech-icons#readme"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/zhiweio/tech-icons"

# Use the same venv path as the builder stage
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Install minimal runtime deps (libgomp1 is required by sentence-transformers/numpy)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system --gid 1000 appuser && \
    useradd --system --uid 1000 --gid appuser --create-home appuser

# Copy the virtual env and source from builder — venv at /opt/venv, same path as builder
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --from=builder --chown=appuser:appuser /build/pyproject.toml /build/uv.lock* /build/tech_icons /app/

# Copy entrypoint
COPY --chown=appuser:appuser docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

WORKDIR /app

# Pre-compile .pyc files for faster startup
RUN python -c "import compileall; compileall.compile_path()" 2>/dev/null || true

USER appuser

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8765/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
