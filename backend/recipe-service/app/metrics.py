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

# Recipe-specific metrics
recipe_operations_total = Counter(
    "recipe_operations_total",
    "Total recipe operations",
    ["operation", "status"]
)

recipe_search_total = Counter(
    "recipe_search_total",
    "Total recipe searches",
    ["query_type", "status"]
)

recipe_count = Gauge(
    "recipe_count",
    "Total number of recipes",
    ["cuisine"]
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

# Recipe complexity metrics
recipe_complexity_score = Gauge(
    "recipe_complexity_score",
    "Complexity score of recipes",
    ["recipe_id"]
)

# Recipe popularity metrics
recipe_views_total = Counter(
    "recipe_views_total",
    "Total recipe views",
    ["recipe_id"]
)

recipe_favorites_total = Counter(
    "recipe_favorites_total",
    "Total recipe favorites",
    ["recipe_id"]
)

def init_metrics(app):
    """Initialize Prometheus metrics for the FastAPI application."""
    Instrumentator().instrument(app).expose(app) 