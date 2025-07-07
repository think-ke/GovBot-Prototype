FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY analytics/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY analytics/ ./analytics/

# Set Python path to include the current directory  
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/analytics/health || exit 1

# Run the application
CMD ["python", "-m", "analytics.main"]
