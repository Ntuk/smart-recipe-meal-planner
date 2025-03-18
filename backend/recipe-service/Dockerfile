FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for Prometheus metrics
RUN mkdir -p /tmp && chmod 777 /tmp

COPY . .

EXPOSE 8000 9090

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 