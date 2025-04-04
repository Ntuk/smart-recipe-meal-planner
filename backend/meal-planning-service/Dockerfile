FROM python:3.9-slim

WORKDIR /app

COPY meal-planning-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for Prometheus metrics
RUN mkdir -p /tmp && chmod 777 /tmp

# Copy the shared module first
COPY shared /app/shared

# Copy the service code
COPY meal-planning-service/app /app/app

EXPOSE 8003 9093

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"] 