FROM python:3.11-slim

LABEL org.opencontainers.image.description="strands-multi-engineer-agent"

# Avoid .pyc files and ensure stdout/stderr are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy dependency metadata first (layer-cache friendly)
COPY pyproject.toml ./

# Install the package in editable mode so CLI entrypoint is registered
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["agent"]
CMD ["--help"]
