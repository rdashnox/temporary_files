"""RabbitMQ consumer for Notification service events.

Consumes order.created and inventory.low_stock events from finmark.events and
writes idempotent in-app notifications into the Notification DB.
"""

from __future__ import annotations

import json

from backend.enterprise.config import enterprise_settings
from backend.enterprise.databases import NotificationSessionLocal, session_scope
from backend.enterprise.services.notification_enterprise_service import process_integration_event


def main() -> None:
    try:
        import pika  # type: ignore
    except Exception as exc:
        raise SystemExit("pika is required for the notification consumer. Run pip install -r requirements.txt") from exc

    params = pika.URLParameters(enterprise_settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="finmark.events", exchange_type="topic", durable=True)
    channel.queue_declare(queue="notification-service.events", durable=True)
    channel.queue_bind(exchange="finmark.events", queue="notification-service.events", routing_key="order.created")
    channel.queue_bind(exchange="finmark.events", queue="notification-service.events", routing_key="inventory.low_stock")

    def handle_message(ch, method, properties, body):
        try:
            event_message = json.loads(body.decode("utf-8"))
            with session_scope(NotificationSessionLocal) as db:
                process_integration_event(db, event_message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue="notification-service.events", on_message_callback=handle_message)
    print("Notification consumer started. Waiting for events...")
    try:
        channel.start_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
