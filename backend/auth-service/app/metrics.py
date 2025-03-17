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

# Authentication metrics
auth_operations_total = Counter(
    "auth_operations_total",
    "Total authentication operations",
    ["operation", "status"]
)

login_attempts_total = Counter(
    "login_attempts_total",
    "Total login attempts",
    ["status"]
)

token_operations_total = Counter(
    "token_operations_total",
    "Total token operations",
    ["operation", "status"]
)

active_tokens = Gauge(
    "active_tokens",
    "Number of active tokens",
    ["user_id"]
)

# User management metrics
user_operations_total = Counter(
    "user_operations_total",
    "Total user operations",
    ["operation", "status"]
)

user_count = Gauge(
    "user_count",
    "Total number of users",
    ["status"]
)

# Security metrics
failed_auth_attempts = Counter(
    "failed_auth_attempts",
    "Total failed authentication attempts",
    ["reason"]
)

password_reset_attempts = Counter(
    "password_reset_attempts",
    "Total password reset attempts",
    ["status"]
)

# Session metrics
active_sessions = Gauge(
    "active_sessions",
    "Number of active sessions",
    ["user_id"]
)

session_duration_seconds = Histogram(
    "session_duration_seconds",
    "Session duration in seconds",
    ["user_id"]
)

# Rate limiting metrics
rate_limit_hits = Counter(
    "rate_limit_hits",
    "Total rate limit hits",
    ["endpoint"]
)

rate_limit_exceeded = Counter(
    "rate_limit_exceeded",
    "Total rate limit exceeded events",
    ["endpoint"]
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

def init_metrics(app):
    """Initialize Prometheus metrics for the FastAPI application."""
    Instrumentator().instrument(app).expose(app) 