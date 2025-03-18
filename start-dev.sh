#!/bin/bash

# Parse command line arguments
MONITOR=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --monitor) MONITOR=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Stop any existing MongoDB container
echo "Stopping any existing MongoDB container..."
docker stop mongodb 2>/dev/null || true

# Start MongoDB and RabbitMQ
echo "Starting MongoDB and RabbitMQ..."
docker compose up -d mongodb rabbitmq
sleep 5  # Wait for services to start

# Export environment variables
export RABBITMQ_URI="amqp://admin:password@localhost:5672/"
export MONGO_URI="mongodb://admin:password@localhost:27017"

# Store the root directory
ROOT_DIR=$(pwd)

# Start services
echo "Starting Auth Service..."
cd $ROOT_DIR/backend/auth-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

echo "Starting Recipe Service..."
cd $ROOT_DIR/backend/recipe-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &

echo "Starting Ingredient Scanner Service..."
cd $ROOT_DIR/backend/ingredient-scanner-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 &

echo "Starting Meal Planning Service..."
cd $ROOT_DIR/backend/meal-planning-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8003 &

echo "Starting Shopping List Service..."
cd $ROOT_DIR/backend/shopping-list-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004 &

echo "Starting Frontend..."
cd $ROOT_DIR/frontend
npm run dev &

# Start monitoring services if --monitor flag is set
if [ "$MONITOR" = true ]; then
    echo "Starting monitoring services..."
    cd $ROOT_DIR
    docker compose -f docker-compose.yml up -d prometheus grafana
    echo "Monitoring services started!"
    echo "Grafana: http://localhost:3000"
    echo "Prometheus: http://localhost:9090"
fi

cd $ROOT_DIR

echo "All services started!"
echo "Frontend: http://localhost:5173"
echo "Auth Service: http://localhost:8000"
echo "Recipe Service: http://localhost:8001"
echo "Ingredient Scanner Service: http://localhost:8002"
echo "Meal Planning Service: http://localhost:8003"
echo "Shopping List Service: http://localhost:8004"

# Wait for user to press Ctrl+C
echo "Press Ctrl+C to stop all services"
wait