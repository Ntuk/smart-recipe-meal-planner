# Smart Recipe & Meal Planner

A microservices-based distributed application that suggests meal plans based on available ingredients, dietary preferences, and user history. This project was developed as part of the Microservices and Containers course (KM00DT91-3005).

## Project Overview

The Smart Recipe & Meal Planner is designed to solve a common problem: "What can I cook with the ingredients I have?" By leveraging microservices architecture and OCR technology, the system can:

- Scan and identify ingredients from handwritten lists using OCR technology
- Match available ingredients with suitable recipes
- Generate personalized meal plans based on dietary preferences
- Create shopping lists for missing ingredients
- Manage user authentication and profiles

## Domain-Driven Design

The Smart Recipe & Meal Planner implements Domain-Driven Design (DDD) principles with the following bounded contexts and their corresponding microservices:

| Bounded Context | Microservice | Core Responsibilities |
|-----------------|--------------|------------------------|
| User Management | Authentication Service | User registration, login, profile management, JWT token handling |
| Ingredient Management | Ingredient Scanner Service | Extracts ingredients from images using OCR, manages user's available ingredients |
| Recipe Catalog | Recipe Service | Stores and retrieves recipes, provides search and filtering capabilities |
| Meal Planning | Meal Planning Service | Generates meal plans based on available ingredients and user preferences |
| Shopping | Shopping List Service | Creates and manages shopping lists for missing ingredients |

## Microservices Architecture

![Smart Recipe & Meal Planner Architecture](/frontend/docs/images/architecture.png)

## Data Flow & Communication

The system implements a hybrid communication model:

### Synchronous Communication (REST APIs)
- Frontend → Auth Service: User registration, login, profile management
- Frontend → Recipe Service: Fetch recipes, filter by ingredients/tags
- Frontend → Ingredient Scanner Service: Upload images for OCR processing
- Frontend → Meal Planning Service: Generate meal plans based on preferences
- Frontend → Shopping List Service: Create and manage shopping lists
- Meal Planning Service → Recipe Service: Fetch recipes for meal plan creation

### Asynchronous Communication (Event-Driven)
The system uses RabbitMQ for event-driven communication between services:

- Ingredient Scanner Service → Meal Planning Service: When new ingredients are detected, the Meal Planning Service is notified to suggest recipes
- Meal Planning Service → Shopping List Service: When a meal plan is created, the Shopping List Service generates a list of missing ingredients
- Services → Frontend: Real-time updates are pushed to the frontend when data changes
- Auth Service → Other Services: User authentication events are broadcast to relevant services

## Tech Stack

### Frontend
- Framework: React with TypeScript
- UI: Tailwind CSS
- Build Tool: Vite
- State Management: React Query for server state, Context API for auth state
- Routing: React Router for navigation

### Backend
- API Framework: FastAPI (Python)
- Database: MongoDB (document-based NoSQL)
- Authentication: JWT-based authentication with refresh tokens
- OCR: Tesseract OCR for ingredient detection
- Messaging: RabbitMQ for event-driven architecture
- API Gateway: Nginx for routing and load balancing

### Infrastructure
- Containerization: Docker
- Orchestration: Docker Compose

## Database Schema

Each microservice maintains its own data store in MongoDB:

### User Collection
```json
{
  "_id": "ObjectId(567890)",
  "username": "johndoe",
  "email": "john@example.com",
  "hashed_password": "hashed_password_string",
  "preferences": {
    "dietary_preferences": ["Vegetarian", "Low-Carb"],
    "favorite_cuisines": ["Italian", "Mexican"]
  },
  "created_at": "2025-03-10T12:00:00Z"
}
```

### Recipe Service Collection
```json
{
  "_id": "ObjectId(123456)",
  "title": "Spaghetti Carbonara",
  "description": "A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.",
  "ingredients": ["Spaghetti", "Eggs", "Pancetta", "Parmesan cheese", "Black pepper", "Salt"],
  "instructions": ["Cook pasta...", "Mix eggs and cheese...", "Combine and serve..."],
  "prep_time_minutes": 10,
  "cook_time_minutes": 15,
  "servings": 4,
  "tags": ["Italian", "Pasta", "Quick"],
  "cuisine": "Italian",
  "difficulty": "Easy",
  "nutritional_info": {
    "calories": 450,
    "protein": 20,
    "carbs": 50,
    "fat": 18
  },
  "created_at": "2025-03-10T12:00:00Z"
}
```

### Ingredient Scanner Collection
```json
{
  "_id": "ObjectId(789012)",
  "user_id": "user123",
  "ingredients": ["Tomatoes", "Onions", "Garlic", "Olive Oil"],
  "image_url": "https://storage.example.com/images/scan123.jpg",
  "scanned_at": "2025-03-15T14:30:00Z"
}
```

### Meal Plan Collection
```json
{
  "_id": "ObjectId(345678)",
  "user_id": "user123",
  "name": "Weekly Plan",
  "recipes": ["recipe_id_1", "recipe_id_2", "recipe_id_3"],
  "days": 7,
  "dietary_preferences": ["Vegetarian", "Low-Carb"],
  "created_at": "2025-03-16T09:15:00Z"
}
```

### Shopping List Collection
```json
{
  "_id": "ObjectId(901234)",
  "user_id": "user123",
  "meal_plan_id": "meal_plan_id_1",
  "name": "Grocery List",
  "items": [
    {"ingredient": "Chicken", "quantity": "500g", "checked": false},
    {"ingredient": "Broccoli", "quantity": "1 head", "checked": true}
  ],
  "created_at": "2025-03-16T10:30:00Z"
}
```

## API Endpoints

### Authentication Service
- POST /auth/register - Register a new user
- POST /auth/login - Login and get access token
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout and invalidate tokens
- GET /auth/profile - Get user profile
- PUT /auth/profile - Update user profile

### Recipe Service
- GET /recipes - List all recipes with optional filtering
- GET /recipes/{id} - Get a specific recipe
- POST /recipes - Create a new recipe
- PUT /recipes/{id} - Update a recipe
- DELETE /recipes/{id} - Delete a recipe

### Ingredient Scanner Service
- POST /scan - Upload an image for ingredient detection
- POST /manual-input - Manually input ingredients

### Meal Planning Service
- POST /meal-plans - Create a meal plan based on ingredients and preferences
- GET /meal-plans - List all meal plans
- GET /meal-plans/{id} - Get a specific meal plan
- DELETE /meal-plans/{id} - Delete a meal plan

### Shopping List Service
- POST /shopping-lists - Create a shopping list from a meal plan
- GET /shopping-lists - List all shopping lists
- GET /shopping-lists/{id} - Get a specific shopping list
- PUT /shopping-lists/{id}/items/{ingredient}/check - Check/uncheck an item
- DELETE /shopping-lists/{id} - Delete a shopping list

## Authentication Flow

The application implements a secure JWT-based authentication system:

1. **Registration**: Users register with email and password
2. **Login**: Upon successful login, the Auth Service issues:
   - Access token (short-lived, 15 minutes)
   - Refresh token (longer-lived, 7 days)
3. **Token Usage**: The access token is included in the Authorization header for API requests
4. **Token Refresh**: When the access token expires, the client uses the refresh token to obtain a new access token
5. **Logout**: Invalidates both access and refresh tokens

## Setup Instructions

### Prerequisites
- Node.js (v16+)
- Python (v3.11+)
- Docker and Docker Compose

### Installation
1. Clone the repository
```bash
git clone https://github.com/yourusername/smart-recipe-meal-planner.git
cd smart-recipe-meal-planner
```

2. Start the services
```bash
./start-dev.sh
```

3. Access the application
   - Frontend: http://localhost:5174

### Development

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Backend Services
Each service can be run independently for development:
```bash
cd backend/recipe-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Project Structure
```
smart-recipe-meal-planner/
├── frontend/                 # React frontend application
│   ├── src/                  # React components and code
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API service clients
│   │   ├── hooks/            # Custom React hooks
│   │   ├── context/          # React context providers
│   │   └── types/            # TypeScript type definitions
│   ├── docs/                 # Architecture documentation
│   │   └── images/           # Architecture diagrams
│   └── public/               # Static assets
├── backend/                  # Backend services
│   ├── auth-service/         # Authentication service
│   │   ├── app/              # Application code
│   │   ├── Dockerfile        # Container configuration
│   │   └── requirements.txt  # Python dependencies
│   ├── recipe-service/       # Recipe database service
│   ├── ingredient-scanner-service/ # OCR ingredient detection
│   ├── meal-planning-service/     # Meal planning engine
│   └── shopping-list-service/     # Shopping list generator
└── docker-compose.yml        # Docker compose configuration
```

## Security Considerations

- **Authentication**: JWT-based authentication with refresh tokens for API access
- **Authorization**: Role-based access control for different operations
- **Password Security**: Passwords are hashed using bcrypt with salt
- **Rate Limiting**: Prevents excessive API requests and brute force attacks
- **CORS**: Proper Cross-Origin Resource Sharing configuration
- **Data Validation**: Input validation on all API endpoints
- **Token Management**: Secure handling of access and refresh tokens
- **HTTPS**: All communications are encrypted in production

## Deployment

The application is containerized using Docker and can be deployed to various environments.

## Contributors

- Nico Tukiainen - Developer
