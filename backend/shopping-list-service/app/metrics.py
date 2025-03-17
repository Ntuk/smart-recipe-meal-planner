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

# Shopping list specific metrics
shopping_list_operations_total = Counter(
    "shopping_list_operations_total",
    "Total shopping list operations",
    ["operation", "status"]
)

shopping_list_count = Gauge(
    "shopping_list_count",
    "Total number of shopping lists",
    ["user_id"]
)

items_per_list = Histogram(
    "items_per_list",
    "Number of items in shopping lists",
    ["list_id"]
)

# Item tracking metrics
items_checked_total = Counter(
    "items_checked_total",
    "Total number of items checked/unchecked",
    ["status"]
)

items_added_total = Counter(
    "items_added_total",
    "Total number of items added to lists",
    ["category"]
)

items_removed_total = Counter(
    "items_removed_total",
    "Total number of items removed from lists",
    ["category"]
)

# List sharing metrics
list_shares_total = Counter(
    "list_shares_total",
    "Total number of list shares",
    ["status"]
)

active_shares = Gauge(
    "active_shares",
    "Number of active list shares",
    ["list_id"]
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

# List completion metrics
list_completion_rate = Gauge(
    "list_completion_rate",
    "Rate of completed items in shopping lists",
    ["list_id"]
)

list_completion_time_seconds = Histogram(
    "list_completion_time_seconds",
    "Time taken to complete shopping lists",
    ["list_id"]
)

def init_metrics(app):
    """Initialize Prometheus metrics for the FastAPI application."""
    Instrumentator().instrument(app).expose(app) 