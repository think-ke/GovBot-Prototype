#!/bin/bash
# ChromaDB startup script

# Function to check if docker compose command is available
check_docker_compose() {
  if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "Using docker compose command"
    DOCKER_COMPOSE_CMD="docker compose"
  else
    echo "Error: Docker compose command is not available"
    echo "Please install Docker with Docker Compose support"
    exit 1
  fi
}

# Function to check for .env file and create from example if needed
setup_env_file() {
  if [ ! -f .env ]; then
    if [ -f .env.example ]; then
      echo "No .env file found. Creating from .env.example..."
      cp .env.example .env
      echo "Created .env file. Please edit it to add your credentials."
    else
      echo "Warning: Neither .env nor .env.example found. Environment configuration may be incomplete."
      touch .env
    fi
  else
    echo "Found existing .env file."
  fi
}

# Parse command line arguments
DEV_MODE=false
for arg in "$@"
do
  case $arg in
    --dev|-d)
    DEV_MODE=true
    shift
    ;;
  esac
done

# Set up environment file if needed
setup_env_file

# Set default values
USERNAME=${CHROMA_USERNAME:-thinkAdmin}
PASSWORD=${CHROMA_PASSWORD:-$(openssl rand -base64 12)}
CHROMA_HOST=${CHROMA_HOST:-chroma}
CHROMA_PORT=${CHROMA_PORT:-8000}
DEV_PORT=${CHROMA_DEV_PORT:-8001}

# Check docker compose availability
check_docker_compose

# Display banner
echo "====================================="
if [ "$DEV_MODE" = true ]; then
  echo " ChromaDB Development Server Setup  "
else
  echo "   ChromaDB Server Setup & Startup   "
fi
echo "====================================="

# Check if server.htpasswd exists
if [ ! -f server.htpasswd ]; then
  echo "Generating htpasswd file with credentials..."
  docker run --rm --entrypoint htpasswd httpd:2 -Bbn "$USERNAME" "$PASSWORD" > server.htpasswd
  echo "Created server.htpasswd with username: $USERNAME"
  
  # Update .env file with the credentials if it exists
  if [ -f .env ]; then
    # Check if CHROMA_CLIENT_AUTHN_CREDENTIALS already exists in .env
    if grep -q "CHROMA_CLIENT_AUTHN_CREDENTIALS" .env; then
      # Replace the existing line
      sed -i "s/CHROMA_CLIENT_AUTHN_CREDENTIALS=.*/CHROMA_CLIENT_AUTHN_CREDENTIALS=$USERNAME:$PASSWORD/" .env
    else
      # Add the line at the end of the file
      echo "CHROMA_CLIENT_AUTHN_CREDENTIALS=$USERNAME:$PASSWORD" >> .env
    fi
    echo "Updated .env file with credentials"
  else
    echo "Warning: .env file not found. Please set CHROMA_CLIENT_AUTHN_CREDENTIALS=$USERNAME:$PASSWORD manually."
  fi
else
  echo "Using existing server.htpasswd file"
fi

# Start ChromaDB using docker compose
echo "Starting ChromaDB server..."
cd "$(dirname "$0")"

# Create development data directory if needed
if [ "$DEV_MODE" = true ]; then
  mkdir -p chroma-dev-data
  
  echo "Starting ChromaDB in development mode..."
  
  # Stop any existing dev container to avoid conflicts
  docker stop chromadb-dev 2>/dev/null || true
  
  # Use absolute paths for volume mounting to avoid path issues
  CURRENT_DIR=$(pwd)
  
  echo "Using directory: $CURRENT_DIR for ChromaDB data"
  echo "Server htpasswd path: $CURRENT_DIR/server.htpasswd"
  
  # Check if server.htpasswd exists before starting container
  if [ ! -f "$CURRENT_DIR/server.htpasswd" ]; then
    echo "Error: server.htpasswd file not found at $CURRENT_DIR/server.htpasswd"
    exit 1
  fi
  
  # Use a different port and directory for development mode with simplified environment variables
  echo "Development ChromaDB instance running on port: $DEV_PORT"
  
  # Update .env.dev file with the dev credentials
  echo "Updating .env.dev file..."
  
  # Create a backup of existing .env.dev if it exists
  if [ -f .env.dev ]; then
    cp .env.dev .env.dev.bak
    echo "Created backup of existing .env.dev as .env.dev.bak"
  fi
  
  if [ -f .env ]; then
    # Start with a copy of the main .env file
    cp .env .env.dev
  else 
    # Create new .env.dev file
    touch .env.dev
  fi
  
  # Update or add CHROMA_PORT
  if grep -q "CHROMA_PORT" .env.dev; then
    sed -i "s/CHROMA_PORT=.*/CHROMA_PORT=$CHROMA_PORT/" .env.dev
  else
    echo "CHROMA_PORT=$CHROMA_PORT" >> .env.dev
  fi
  
  # Add CHROMA_DEV_PORT to .env.dev
  if grep -q "CHROMA_DEV_PORT" .env.dev; then
    sed -i "s/CHROMA_DEV_PORT=.*/CHROMA_DEV_PORT=$DEV_PORT/" .env.dev
  else
    echo "CHROMA_DEV_PORT=$DEV_PORT" >> .env.dev
  fi
  
  # Update CHROMA_HOST if needed
  if grep -q "CHROMA_HOST" .env.dev; then
    sed -i "s/CHROMA_HOST=.*/CHROMA_HOST=chroma-dev/" .env.dev
  else
    echo "CHROMA_HOST=chroma-dev" >> .env.dev
  fi
  
  # Update or add authentication credentials
  if grep -q "CHROMA_CLIENT_AUTHN_CREDENTIALS" .env.dev; then
    sed -i "s/CHROMA_CLIENT_AUTHN_CREDENTIALS=.*/CHROMA_CLIENT_AUTHN_CREDENTIALS=$USERNAME:$PASSWORD/" .env.dev
  else
    echo "CHROMA_CLIENT_AUTHN_CREDENTIALS=$USERNAME:$PASSWORD" >> .env.dev
  fi
  
  echo "Updated .env.dev file with development ChromaDB settings"
  
  # Check if docker-compose.dev.yml exists
  if [ -f "docker-compose.dev.yml" ]; then
    echo "Development environment setup complete. To start the server, run:"
    echo "$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d"
  else
    echo "docker-compose.dev.yml not found, setup complete. To start the server, run:"
    echo "docker run -d --name chromadb-dev \\"
    echo "  -v \"$CURRENT_DIR/chroma-dev-data:/chroma/chroma\" \\"
    echo "  -v \"$CURRENT_DIR/server.htpasswd:/chroma/server.htpasswd:ro\" \\"
    echo "  -p $DEV_PORT:8000 \\"
    echo "  -e AUTH_CREDENTIALS_FILE=/chroma/server.htpasswd \\"
    echo "  -e AUTH_PROVIDER=basic \\"
    echo "  chromadb/chroma:latest"
  fi
else
  # Check if docker-compose.yml exists in a chroma directory
  if [ -d "chroma" ] && [ -f "chroma/docker-compose.yml" ]; then
    cd chroma
    echo "ChromaDB setup complete. To start the server, run:"
    echo "$DOCKER_COMPOSE_CMD up -d --build"
  else
    echo "ChromaDB setup complete. Server not started."
    echo "To start ChromaDB as a standalone container, run:"
    
    CURRENT_DIR=$(pwd)
    
    echo "docker run -d --name chromadb \\"
    echo "  -v \"$CURRENT_DIR/chroma:/chroma/chroma\" \\"
    echo "  -v \"$CURRENT_DIR/server.htpasswd:/chroma/server.htpasswd:ro\" \\"
    echo "  -p 8000:8000 \\"
    echo "  -e AUTH_CREDENTIALS_FILE=/chroma/server.htpasswd \\"
    echo "  -e AUTH_PROVIDER=basic \\"
    echo "  chromadb/chroma:latest"
  fi
fi

echo "====================================="
echo "ChromaDB setup completed successfully."
if [ "$DEV_MODE" = true ]; then
  echo "Development mode configuration ready."
  echo "Host: localhost"
  echo "Port: $DEV_PORT"
else
  echo "Host: $CHROMA_HOST"
  echo "Port: $CHROMA_PORT"
fi
echo "Authentication: Basic auth with username: $USERNAME"
echo "====================================="