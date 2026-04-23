# Multi-stage Dockerfile for optimized image size and build performance

# Stage 1: Build Rust native library
FROM rust:1.81-slim AS rust-builder
WORKDIR /build
# Copy only manifest first for better layer caching
COPY native/Cargo.toml native/Cargo.lock ./native/
# Create a dummy source file to pre-fetch dependencies
RUN mkdir -p native/src && echo "fn main() {}" > native/src/lib.rs
RUN cd native && cargo build --release || true
# Now copy the real source and build
COPY native/src ./native/src
RUN cd native && cargo build --release

# Stage 2: Build Python environment
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

# Stage 3: Final runtime image
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

# Copy application source
COPY . .

# Copy compiled Rust library from rust-builder
# Place in ddgs/data/ with names expected by utils_native.py
# Note: we copy libddgs_native.so and rename it to match the expected architecture-specific name
# On standard linux amd64, it expects libddgs_native_linux_amd64.so
RUN mkdir -p ddgs/data
COPY --from=rust-builder /build/native/target/release/libddgs_native.so ./ddgs/data/libddgs_native_linux_amd64.so
COPY --from=rust-builder /build/native/target/release/libddgs_native.so ./ddgs/data/libddgs_native.so

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
