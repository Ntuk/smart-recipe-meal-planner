from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# OCR metrics
ocr_operations_total = Counter(
    "ocr_operations_total",
    "Total number of OCR operations",
    ["operation", "status"]
)

ocr_processing_time_seconds = Histogram(
    "ocr_processing_time_seconds",
    "Time taken to process OCR operations",
    ["operation"]
)

ocr_confidence_score = Gauge(
    "ocr_confidence_score",
    "OCR confidence score for processed images",
    ["image_id"]
)

# Ingredient detection metrics
ingredients_detected_total = Counter(
    "ingredients_detected_total",
    "Total number of ingredients detected",
    ["status"]
)

ingredients_per_image = Histogram(
    "ingredients_per_image",
    "Number of ingredients detected per image",
    ["status"]
)

# Database metrics
db_operations_total = Counter(
    "db_operations_total",
    "Total number of database operations",
    ["operation", "status"]
)

# Queue metrics
queue_size = Gauge(
    "queue_size",
    "Current size of the processing queue"
)

queue_processing_time = Histogram(
    "queue_processing_time",
    "Time taken to process items from queue",
    ["operation"]
)

def init_metrics(app):
    """Initialize Prometheus metrics for the FastAPI application."""
    Instrumentator().instrument(app).expose(app) 