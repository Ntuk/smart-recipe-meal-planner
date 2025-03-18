import logging
import sys

def setup_logging():
    """Configure logging for all services"""
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Set specific loggers to WARNING level to reduce noise
    logging.getLogger('pika').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('pika.adapters').setLevel(logging.WARNING)
    logging.getLogger('pika.channel').setLevel(logging.WARNING)
    logging.getLogger('pika.connection').setLevel(logging.WARNING)
    logging.getLogger('pika.adapters.utils').setLevel(logging.WARNING)
    
    # Log startup message
    logging.info("Logging configured successfully") 