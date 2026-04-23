# Multi-stage Dockerfile for optimized image size and build performance
# Note: This Dockerfile expects the native Rust library (libddgs_native.so)
# to already be built and located in ddgs/data/. This is handled automatically
# by the GitHub Actions CI/CD pipeline before building the Docker image.

# Stage 1: Build Python environment
FROM python:3.11-slim AS python-builder
WORKDIR /build
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# Copy project metadata
COPY pyproject.toml README.md ./
# Create dummy package to satisfy dynamic versioning and dependencies
RUN mkdir ddgs && echo "__version__ = '1.0.0'" > ddgs/__init__.py
# Install dependencies into /root/.local
RUN pip install --user .[api]

# Stage 2: Final runtime image
FROM python:3.11-slim AS runtime
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/home/app/.local/bin:${PATH}"

# Install minimal runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app/metasearch

# Copy installed Python packages from builder
COPY --from=python-builder /root/.local /home/app/.local

# Copy application source (which MUST include ddgs/data/libddgs_native.so)
COPY . .

# Ensure correct names for architecture-specific native loading
# If libddgs_native.so exists but architecture specific name doesn't, copy it
RUN if [ -f "ddgs/data/libddgs_native.so" ] && [ ! -f "ddgs/data/libddgs_native_linux_amd64.so" ]; then \
        cp ddgs/data/libddgs_native.so ddgs/data/libddgs_native_linux_amd64.so; \
    fi

# Ensure correct permissions
RUN chown -R app:app /home/app

USER app

# Expose API port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the API server via uvicorn
CMD ["python", "-m", "uvicorn", "ddgs.api_server:fastapi_app", "--host", "0.0.0.0", "--port", "8000"]
