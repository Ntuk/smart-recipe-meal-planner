#!/bin/bash

# Array of service directories
services=(
    "auth-service"
    "recipe-service"
    "ingredient-scanner-service"
    "meal-planning-service"
    "shopping-list-service"
)

# Install dependencies for each service
for service in "${services[@]}"; do
    echo "Installing dependencies for $service..."
    cd "backend/$service" || exit
    pip install -r requirements.txt
    cd ../.. || exit
done

echo "All dependencies installed!" 