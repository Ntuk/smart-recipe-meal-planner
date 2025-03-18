import pika
import json
import uuid

# Connect to RabbitMQ
credentials = pika.PlainCredentials('admin', 'password')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='rabbitmq',
        port=5672,
        credentials=credentials
    )
)
channel = connection.channel()

# Declare the exchange
channel.exchange_declare(exchange='ingredients', exchange_type='topic', durable=True)

# Prepare the test message
test_message = {
    "scan_id": str(uuid.uuid4()),
    "user_id": "test_user_123",
    "ingredients": ["Tomatoes", "Onions", "Garlic", "Olive Oil"],
    "timestamp": "2024-03-19T12:00:00Z"
}

# Publish the message
channel.basic_publish(
    exchange='ingredients',
    routing_key='ingredient.detected',
    body=json.dumps(test_message)
)

print(f" [x] Sent test message: {test_message}")

# Close the connection
connection.close() 