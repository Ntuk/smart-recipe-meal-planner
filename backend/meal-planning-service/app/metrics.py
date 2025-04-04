from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Meal planning specific metrics
meal_plan_operations_total = Counter(
    "meal_plan_operations_total",
    "Total meal plan operations",
    ["operation", "status"]
)

meal_plan_generation_total = Counter(
    "meal_plan_generation_total",
    "Total meal plan generations",
    ["status"]
)

meal_plan_generation_time_seconds = Histogram(
    "meal_plan_generation_time_seconds",
    "Time taken to generate meal plans",
    ["plan_type"]
)

meal_plan_count = Gauge(
    "meal_plan_count",
    "Total number of meal plans",
    ["user_id"]
)

# Nutrition metrics
nutrition_goals_met = Gauge(
    "nutrition_goals_met",
    "Percentage of nutrition goals met",
    ["user_id", "plan_id"]
)

calorie_variance = Gauge(
    "calorie_variance",
    "Variance from target calories",
    ["user_id", "plan_id"]
)

# Database metrics
db_operations_total = Counter(
    "db_operations_total",
    "Total database operations",
    ["operation", "status"]
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"]
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"]
)

# Recipe recommendation metrics
recipe_recommendations_total = Counter(
    "recipe_recommendations_total",
    "Total recipe recommendations",
    ["status"]
)

recipe_recommendation_accuracy = Gauge(
    "recipe_recommendation_accuracy",
    "Accuracy of recipe recommendations",
    ["user_id"]
)

# User preference metrics
preference_violations_total = Counter(
    "preference_violations_total",
    "Total preference violations",
    ["preference_type"]
)

# Prometheus metrics
REQUESTS = Counter('meal_planning_service_requests_total', 'Total requests to the meal planning service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('meal_planning_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
PLAN_OPERATIONS = Counter('meal_planning_service_operations_total', 'Total meal plan operations', ['operation', 'status'])

def init_metrics(app):
    """Initialize Prometheus metrics for the FastAPI application."""
    Instrumentator().instrument(app).expose(app) 