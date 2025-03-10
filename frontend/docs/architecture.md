Smart Recipe & Meal Planner - System Architecture

1️⃣ Overview

This document describes the microservice-based architecture for the Smart Recipe & Meal Planner application. The system consists of multiple microservices, each responsible for a distinct function, communicating through REST APIs and optionally via event-driven messaging.

2️⃣ Microservices Overview

Service Name

Responsibility

Frontend (React)

UI for users to interact with recipes, meal plans, and shopping lists.

Recipe Service

Stores and manages recipes. Provides search and filtering.

Ingredient Scanner Service

Uses OCR to detect ingredients from images.

Meal Planning Service

Suggests meals based on dietary preferences and available ingredients.

Shopping List Service

Creates shopping lists for missing ingredients.

MongoDB (Database)

Stores recipes, scanned ingredients, meal plans, and shopping lists.

OCR API (Tesseract/Google Vision)

Extracts ingredients from images scanned by the Ingredient Scanner Service.

RabbitMQ/Kafka (Optional)

For event-driven communication between services.

3️⃣ Data Flow & Communication

The system follows a hybrid communication model, combining REST APIs for synchronous interactions and RabbitMQ/Kafka for asynchronous messaging.

3.1 API Flow (REST Communication)

Frontend → Recipe Service: Fetch available recipes (GET /recipes).

Frontend → Ingredient Scanner Service: Upload an image for OCR processing (POST /scan).

Frontend → Meal Planning Service: Request meal plan suggestions (POST /plan).

Frontend → Shopping List Service: Retrieve shopping lists (GET /shopping-list).

3.2 Event Flow (Message Queue - Optional)

Ingredient Scanner Service publishes IngredientExtracted event → Recipe Service updates ingredient data.

Meal Planning Service publishes MealPlanCreated event → Shopping List Service generates a list.

Shopping List Service publishes ShoppingListUpdated event → Frontend gets real-time updates.

4️⃣ API Contracts

Each microservice exposes RESTful APIs. The OpenAPI specifications are stored in /docs/api-specs/.

Example for Recipe Service:

openapi: 3.0.0
info:
  title: Recipe Service API
  version: 1.0.0
paths:
  /recipes:
    get:
      summary: Get all recipes
      responses:
        "200":
          description: A list of recipes

5️⃣ Database Schema (MongoDB)

Each microservice has its own MongoDB collection:

recipes: Stores recipes and ingredients.

scanned_ingredients: Stores extracted OCR data.

meal_plans: Stores generated meal plans.

shopping_lists: Stores shopping list details.

Example schema for a Recipe document:

{
  "_id": "ObjectId(123456)",
  "name": "Spaghetti Bolognese",
  "ingredients": ["Tomatoes", "Minced Meat", "Garlic", "Pasta"],
  "instructions": "Cook pasta and mix with sauce.",
  "created_at": "2025-03-10T12:00:00Z"
}

6️⃣ Deployment Strategy

Each microservice runs inside Docker containers and can be orchestrated using Docker Compose or Kubernetes.

Containerized Services

Service

Image

Frontend

frontend:latest

Recipe Service

recipe-service:latest

Ingredient Scanner Service

ingredient-scanner-service:latest

Meal Planning Service

meal-planning-service:latest

Shopping List Service

shopping-list-service:latest

MongoDB

mongo:latest

RabbitMQ/Kafka (Optional)

rabbitmq:latest or kafka:latest

7️⃣ Security Considerations

Authentication: OAuth/JWT-based authentication for API access.

Rate Limiting: Prevent excessive API requests with rate limiting middleware.

CORS Handling: Ensure proper Cross-Origin Resource Sharing (CORS) configuration.

8️⃣ Future Enhancements

Implement GraphQL API for flexible data fetching.

Add monitoring service (e.g., Prometheus + Grafana) for performance tracking.

Enhance AI-based ingredient suggestions for meal planning.