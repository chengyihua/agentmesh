FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging files
COPY pyproject.toml README.md ./
COPY src/agentmesh/__init__.py src/agentmesh/

# Install dependencies (using pip install . to parse pyproject.toml)
RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels dist/*.whl && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels redis asyncpg psycopg2-binary fastapi uvicorn pydantic python-multipart python-jose[cryptography] httpx

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user
RUN groupadd -r agentmesh && useradd -r -g agentmesh agentmesh

# Copy built wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/dist/*.whl /wheels/

# Install the application and dependencies from wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Change ownership
RUN chown -R agentmesh:agentmesh /app

# Switch to non-root user
USER agentmesh

# Expose API port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
# We use standard CMD to allow overriding args gracefully
CMD ["python", "-m", "agentmesh", "serve", "--storage", "memory", "--host", "0.0.0.0", "--port", "8000"]
