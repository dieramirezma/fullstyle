import pika
import json
import os
import time
import threading
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class RabbitMQConnection:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RabbitMQConnection, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqp://localhost')
        self.connection = None
        self.channel = None
        self._initialized = True
        
    def connect(self, max_retries=30, delay=2):
        """
        Conecta a RabbitMQ con reintentos
        """
        if self.connection and not self.connection.is_closed:
            return
            
        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Attempting to connect to RabbitMQ (attempt {retries + 1}/{max_retries})...")
                parameters = pika.URLParameters(self.rabbitmq_url)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declarar la cola de emails
                self.channel.queue_declare(queue='email_queue', durable=True)
                logger.info("Successfully connected to RabbitMQ!")
                return
                
            except Exception as e:
                retries += 1
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                if retries < max_retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached. Unable to connect to RabbitMQ.")
                    raise e
    
    def get_connection(self):
        """
        Obtiene una nueva conexión para el consumer
        """
        parameters = pika.URLParameters(self.rabbitmq_url)
        return pika.BlockingConnection(parameters)
    
    def publish_message(self, queue_name, message):
        """
        Publica un mensaje usando una conexión separada
        """
        connection = None
        try:
            # Usar una conexión separada para publicar
            parameters = pika.URLParameters(self.rabbitmq_url)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Declarar la cola
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Publicar el mensaje
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                )
            )
            logger.info(f"Message published to queue {queue_name}")
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise e
        finally:
            if connection and not connection.is_closed:
                connection.close()
    
    def close_connection(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Instancia global de RabbitMQ
rabbitmq = RabbitMQConnection()