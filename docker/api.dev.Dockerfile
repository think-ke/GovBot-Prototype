# Use an official Python runtime as a parent image
FROM python:3.11

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

# Install development dependencies
RUN pip install --no-cache-dir gunicorn uvloop uvicorn[standard] watchfiles

# Copy the application code
COPY ./app /app/app

# Make port 5005 available to the world outside this container
EXPOSE 5005

# Use uvicorn with hot reload for development
CMD ["gunicorn", "app.api.fast_api_app:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5005",  "--reload"]
