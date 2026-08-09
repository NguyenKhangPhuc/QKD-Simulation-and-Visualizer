# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy requirements file first to utilize Docker layer cache
COPY requirements.txt .

# Create a virtual environment and install dependencies without cache
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runner stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Set essential Python environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy the pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create a secure non-root user and group
RUN groupadd -g 1000 appgroup && \
    useradd -r -u 1000 -g appgroup -m -s /bin/sbin appuser

# Copy application source code and adjust ownership
COPY --chown=appuser:appgroup alice_client.py bob_server.py ./

# Expose API ports
EXPOSE 8000
EXPOSE 8001

# Switch to the non-root user for security hardening
USER appuser

# Default CMD (can be overridden in docker-compose)
CMD ["uvicorn", "alice_client:app", "--host", "0.0.0.0", "--port", "8001"]
