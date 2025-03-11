# Smart Recipe & Meal Planner

A microservice-based application for managing recipes, planning meals, and generating shopping lists.

## Features

- User authentication and profile management
- Recipe database with search and filtering
- Ingredient scanning from images using OCR
- Meal planning with calendar integration
- Shopping list generation based on meal plans

## Architecture

The application is built using a microservice architecture with the following services:

- **Auth Service**: Handles user authentication and profile management
- **Recipe Service**: Manages recipes and provides search functionality
- **Ingredient Scanner Service**: Extracts ingredients from images using OCR
- **Meal Planning Service**: Creates and manages meal plans
- **Shopping List Service**: Generates shopping lists based on meal plans

## Tech Stack

### Frontend
- React
- TypeScript
- Tailwind CSS
- Axios for API communication

### Backend
- FastAPI (Python)
- MongoDB for data storage
- JWT for authentication
- Docker for containerization

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (v16+)
- Python (v3.9+)

### Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/smart-recipe-meal-planner.git
   cd smart-recipe-meal-planner
   ```

2. Start the development environment:
   ```
   chmod +x start-dev.sh
   ./start-dev.sh
   ```

   This will start:
   - MongoDB on port 27017
   - Auth Service on port 8000
   - Recipe Service on port 8001
   - Ingredient Scanner Service on port 8002
   - Meal Planning Service on port 8003
   - Shopping List Service on port 8004
   - Frontend on port 5173

3. Access the application at http://localhost:5173

### Production Deployment

1. Build and start all services using Docker Compose:
   ```
   docker-compose up -d
   ```

2. Access the application at http://localhost:3000

## API Documentation

Each service provides Swagger documentation at the `/docs` endpoint:

- Auth Service: http://localhost:8000/docs
- Recipe Service: http://localhost:8001/docs
- Ingredient Scanner Service: http://localhost:8002/docs
- Meal Planning Service: http://localhost:8003/docs
- Shopping List Service: http://localhost:8004/docs

## Project Structure

```
smart-recipe-meal-planner/
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── ...
│   ├── Dockerfile           # Frontend Docker configuration
│   └── ...
├── backend/
│   ├── auth-service/        # Authentication service
│   ├── recipe-service/      # Recipe management service
│   ├── ingredient-scanner-service/ # Ingredient scanning service
│   ├── meal-planning-service/ # Meal planning service
│   ├── shopping-list-service/ # Shopping list service
│   └── ...
├── docker-compose.yml       # Docker Compose configuration
├── start-dev.sh             # Development startup script
└── README.md                # Project documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 