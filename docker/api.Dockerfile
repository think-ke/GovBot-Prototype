# Use an official Python runtime as a parent image
FROM python:3.11.12-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Install build-essential and other development dependencies
RUN apt-get update && \
    apt-get install -y build-essential python3-dev libffi-dev && \
    apt-get clean

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn and uvloop
RUN pip install --no-cache-dir gunicorn uvloop uvicorn[standard] watchfiles

# Copy the application code and scripts into the container
COPY ./app /app/app

# Copy any additional scripts or files
COPY ./scripts /app/scripts

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Set environment variable defaults
ENV USE_UVLOOP=false

# Command to run the application
CMD ["uvicorn", "app.api.fast_api_app:app", "--host", "0.0.0.0", "--port", "5000", "--loop", "asyncio", "--http", "httptools"]