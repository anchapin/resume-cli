# =============================================================================
# Stage 1: Build dependencies
# =============================================================================
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt ./
COPY api/requirements.txt ./api/
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r ./api/requirements.txt

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    pandoc \
    texlive-xetex \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    # Create non-root user
    && groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/bin/python /usr/local/bin/python
COPY --from=builder /usr/local/bin/pip /usr/local/bin/pip

# Set working directory
WORKDIR /app

# Copy application code and installation files
COPY --chown=appuser:appgroup pyproject.toml setup.py ./
COPY --chown=appuser:appgroup api/ api/
COPY --chown=appuser:appgroup cli/ cli/
COPY --chown=appuser:appgroup templates/ templates/
COPY --chown=appuser:appgroup config/ config/

# Install the package
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER appuser

# Expose port for API server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Run the API server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
