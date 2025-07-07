FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY tests/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the test suite
COPY tests/ ./tests/
COPY app/ ./app/

# Set Python path
ENV PYTHONPATH=/app

# Expose port for the test service
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the test microservice
CMD ["python", "-m", "tests.scalability_tests.test_service"]
