# Dockerfile for Halal Trading Bot GUI
FROM python:3.11-slim

LABEL maintainer="Halal Trading Bot Team"
LABEL description="Web GUI for managing multiple Halal Trading Bot instances"
LABEL version="2.2.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app

# Set working directory
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc6-dev \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY gui/requirements.txt gui/requirements.txt
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r gui/requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs/bots configs exports data gui/static

# Set permissions
RUN chmod +x gui/deploy.py

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser \
    && chown -R appuser:appuser $APP_HOME
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3002/api/health || exit 1

# Expose port
EXPOSE 3002

# Command to run the application
CMD ["python", "gui/api_server.py"]