# Smart Recipe & Meal Planner

A microservices-based application that suggests meal plans based on available ingredients, dietary preferences, and user history.

## Microservices Architecture

The system consists of four key microservices:

| Microservice | Responsibilities |
|--------------|------------------|
| Recipe Service | Stores & retrieves recipes, categories, and nutritional information |
| Ingredient Scanner Service | Uses OCR to detect ingredients from uploaded images (e.g., grocery lists, fridge contents) |
| Meal Planning Service | Suggests meal plans based on available ingredients, dietary preferences, and user history |
| Shopping List Service | Creates a grocery list for missing ingredients based on meal selection |

## Tech Stack

- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **OCR**: Tesseract OCR or Google Vision API
- **Messaging** (optional): RabbitMQ/Kafka for event-driven architecture

## Setup Instructions

### Prerequisites

- Node.js (v16+)
- Python (v3.9+)
- Docker and Docker Compose

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/smart-recipe-meal-planner.git
cd smart-recipe-meal-planner
```

2. Start the services using Docker Compose
```bash
docker-compose up
```

3. Access the application
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend Services

Each service can be run independently for development:

```bash
cd backend/recipe-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

## Project Structure

```
smart-recipe-meal-planner/
├── frontend/                 # React frontend application
├── backend/                  # Backend services
│   ├── recipe-service/       # Recipe database service
│   ├── ingredient-scanner-service/ # OCR ingredient detection
│   ├── meal-planning-service/     # Meal planning engine
│   └── shopping-list-service/     # Shopping list generator
└── docker-compose.yml        # Docker compose configuration
```

## API Endpoints

- `/api/recipes` - Recipe management
- `/api/ingredients/scan` - Ingredient scanning
- `/api/meal-plans` - Meal planning
- `/api/shopping-list` - Shopping list generation

## License

MIT 