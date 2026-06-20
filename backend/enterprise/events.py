"""Message queue integration with an outbox-friendly publisher.

RabbitMQ is used in Docker/cloud mode. When RabbitMQ is unavailable in local
student environments, the publisher fails gracefully and the event remains in the
service outbox table for retry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import enterprise_settings


@dataclass(frozen=True)
class IntegrationEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    event_id: str = ""
    occurred_at: str = ""

    def to_message(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id or uuid4().hex,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
            "occurred_at": self.occurred_at or datetime.now(timezone.utc).isoformat(),
        }


class EventPublisher:
    exchange_name = "finmark.events"

    def publish(self, event: IntegrationEvent) -> bool:
        if not enterprise_settings.event_bus_enabled:
            return False

        message = event.to_message()
        routing_key = event.event_type
        try:
            import pika  # type: ignore

            params = pika.URLParameters(enterprise_settings.rabbitmq_url)
            connection = pika.BlockingConnection(params)
            try:
                channel = connection.channel()
                channel.exchange_declare(exchange=self.exchange_name, exchange_type="topic", durable=True)
                channel.basic_publish(
                    exchange=self.exchange_name,
                    routing_key=routing_key,
                    body=json.dumps(message, default=str).encode("utf-8"),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type="application/json",
                        message_id=message["event_id"],
                    ),
                )
            finally:
                connection.close()
            return True
        except Exception:
            # Do not crash business transactions just because the broker is down.
            # The outbox row lets a retry worker publish later.
            return False


event_publisher = EventPublisher()
