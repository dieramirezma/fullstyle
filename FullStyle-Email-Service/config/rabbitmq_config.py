"""Bounded connections and publisher confirms. No implicit write retries."""

import json
import os

import pika


class RabbitMQConnection:
    def get_connection(self):
        parameters = pika.URLParameters(os.environ["RABBITMQ_URL"])
        parameters.socket_timeout = 2
        parameters.stack_timeout = 4
        parameters.blocked_connection_timeout = 2
        parameters.connection_attempts = 1
        parameters.heartbeat = 10
        return pika.BlockingConnection(parameters)

    def publish_message(self, queue_name, message):
        connection = self.get_connection()
        try:
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.confirm_delivery()
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(message),
                mandatory=True,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                    message_id=message.get("event_id"),
                ),
            )
        finally:
            if connection.is_open:
                connection.close()


rabbitmq = RabbitMQConnection()
