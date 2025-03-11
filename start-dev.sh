#!/bin/bash

# Stop any existing MongoDB container
echo "Stopping any existing MongoDB container..."
docker stop mongodb 2>/dev/null || true

# Start MongoDB
echo "Starting MongoDB..."
docker compose up -d mongodb
sleep 5  # Wait for MongoDB to start

# Start Auth Service
echo "Starting Auth Service..."
cd backend/auth-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
cd ../..

# Start Recipe Service
echo "Starting Recipe Service..."
cd backend/recipe-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
cd ../..

# Start Ingredient Scanner Service
echo "Starting Ingredient Scanner Service..."
cd backend/ingredient-scanner-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 &
cd ../..

# Start Meal Planning Service
echo "Starting Meal Planning Service..."
cd backend/meal-planning-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003 &
cd ../..

# Start Shopping List Service
echo "Starting Shopping List Service..."
cd backend/shopping-list-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004 &
cd ../..

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev &
cd ..

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