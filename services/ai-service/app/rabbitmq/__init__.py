"""RabbitMQ integration for the AI Service.

Two components:

    - RabbitMQConsumer: subscribes to the price and indicator
      queues and logs incoming events. Best-effort — if RabbitMQ
      is unavailable, the consumer logs a warning and the service
      continues without it.

    - RabbitMQPublisher: a one-shot publish helper used to
      announce events (e.g. ModelsRetrained) on the exchange.
      Also best-effort — publish failures are logged and
      swallowed.

Both are wired into the FastAPI lifespan (consumer) and into
selected scheduler jobs (publisher). The underlying message
broker is aio-pika.

See app/rabbitmq/consumer.py and app/rabbitmq/publisher.py for
the implementation details.
"""

from app.rabbitmq.consumer import RabbitMQConsumer
from app.rabbitmq.publisher import RabbitMQPublisher

__all__ = ["RabbitMQConsumer", "RabbitMQPublisher"]