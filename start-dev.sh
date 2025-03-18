#!/bin/bash

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed. Please install it first."
        exit 1
    fi
}

# Function to check Python version
check_python_version() {
    required_version="3.9"
    current_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "$required_version" "$current_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "Error: Python version must be $required_version or higher (current: $current_version)"
        exit 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    local service_dir=$1
    local service_name=$2
    if [ ! -f "$service_dir/requirements.txt" ]; then
        echo "Error: requirements.txt not found in $service_dir"
        exit 1
    fi
    echo "Installing Python dependencies for $service_name..."
    pip install --quiet -r "$service_dir/requirements.txt"
}

# Function to install Node.js dependencies
install_node_deps() {
    if [ ! -f "package.json" ]; then
        echo "Error: package.json not found in frontend directory"
        exit 1
    fi
    echo "Installing Node.js dependencies..."
    npm install
}

# Check for required tools
echo "Checking dependencies..."
check_command "docker"
check_command "python3"
check_command "pip"
check_command "node"
check_command "npm"
check_python_version

# Parse command line arguments
MONITOR=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --monitor) MONITOR=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Store the root directory
ROOT_DIR=$(pwd)

# Create necessary directories
mkdir -p $ROOT_DIR/data/mongodb
mkdir -p $ROOT_DIR/data/rabbitmq

# Install dependencies for all services
echo "Installing dependencies for all services..."
for service in auth-service recipe-service ingredient-scanner-service meal-planning-service shopping-list-service; do
    cd "$ROOT_DIR/backend/$service"
    install_python_deps . "$service"
done

# Install frontend dependencies
cd "$ROOT_DIR/frontend"
install_node_deps

# Stop any existing containers
echo "Stopping any existing containers..."
docker compose down

# Start MongoDB and RabbitMQ
echo "Starting MongoDB and RabbitMQ..."
cd $ROOT_DIR
docker compose up -d mongodb rabbitmq

# Wait for MongoDB and RabbitMQ to be healthy
echo "Waiting for MongoDB and RabbitMQ to be healthy..."
attempt=1
max_attempts=30
while [ $attempt -le $max_attempts ]; do
    if docker compose ps mongodb | grep -q "healthy" && docker compose ps rabbitmq | grep -q "healthy"; then
        echo "MongoDB and RabbitMQ are healthy!"
        break
    fi
    echo "Waiting for services to be healthy (attempt $attempt/$max_attempts)..."
    sleep 2
    ((attempt++))
done

if [ $attempt -gt $max_attempts ]; then
    echo "Error: Services failed to become healthy within the timeout period"
    exit 1
fi

# Export environment variables
export RABBITMQ_URI="amqp://admin:password@localhost:5672/"
export MONGO_URI="mongodb://admin:password@localhost:27017"
export PYTHONPATH="$ROOT_DIR/backend:$ROOT_DIR/backend/shared:$PYTHONPATH"

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    echo "Starting $service_name..."
    cd "$ROOT_DIR/backend/$service_name"
    PYTHONPATH="$ROOT_DIR/backend:$ROOT_DIR/backend/shared:$PYTHONPATH" python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $port &
    sleep 2  # Give each service a moment to start
}

# Start all services
start_service "auth-service" 8000
start_service "recipe-service" 8001
start_service "ingredient-scanner-service" 8002
start_service "meal-planning-service" 8003
start_service "shopping-list-service" 8004

# Start frontend
echo "Starting Frontend..."
cd "$ROOT_DIR/frontend"
npm run dev &

# Start nginx
echo "Starting nginx..."
cd $ROOT_DIR
docker compose up -d nginx

# Start monitoring services if --monitor flag is set
if [ "$MONITOR" = true ]; then
    echo "Starting monitoring services..."
    cd $ROOT_DIR
    docker compose up -d prometheus grafana mongodb-exporter
    echo "Monitoring services started!"
    echo "Grafana: http://localhost:3000 (admin/admin)"
    echo "Prometheus: http://localhost:9095"
fi

cd $ROOT_DIR

echo "All services started!"
echo "Frontend: http://localhost:3001"
echo "API Gateway: http://localhost:80"
echo "Auth Service: http://localhost:8000"
echo "Recipe Service: http://localhost:8001"
echo "Ingredient Scanner Service: http://localhost:8002"
echo "Meal Planning Service: http://localhost:8003"
echo "Shopping List Service: http://localhost:8004"
echo "RabbitMQ Management: http://localhost:15672 (admin/password)"

# Create a trap to handle Ctrl+C gracefully
trap 'echo "Shutting down services..."; docker compose down; pkill -P $$; exit 0' SIGINT SIGTERM

# Wait for user to press Ctrl+C
echo "Press Ctrl+C to stop all services"
wait