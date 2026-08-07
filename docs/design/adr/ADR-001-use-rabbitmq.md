# ADR-001: Use RabbitMQ for Event-Driven Architecture

## Status

**Accepted**

---

## Context

We need a message broker to enable asynchronous communication between our 4 microservices (Data Ingestion, AI Service, API Gateway, Alert Service).

The broker must support:
- Event publishing and consumption
- Reliable message delivery
- Dead letter queue support
- Retry mechanisms
- Good Python SDK support

---

## Decision

**Use RabbitMQ** as the message broker.

---

## Rationale

| Reason | Explanation |
|--------|-------------|
| **Simplicity** | Easier to set up and maintain than Kafka |
| **Good Fit** | Our event volume is moderate (not millions per second) |
| **Feature Rich** | Supports DLQ, retry, exchanges, queues |
| **Python SDK** | Excellent pika and aio-pika libraries |
| **Cloud-Native** | Works well with Kubernetes |

---

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Apache Kafka** | Higher complexity, overkill for our volume |
| **AWS SQS + SNS** | Vendor lock-in (we may multi-cloud) |
| **Redis Pub/Sub** | No DLQ support, no persistence |
| **Google Pub/Sub** | Vendor lock-in |

---

## Consequences

### Positive

- ✅ Easier to implement and maintain
- ✅ Good community support
- ✅ Excellent Python integration
- ✅ Simple to deploy in Kubernetes

### Negative

- ❌ Lower throughput than Kafka
- ❌ Less built-in persistence

---

## Implementation Details

| Component | Technology |
|-----------|------------|
| Broker | RabbitMQ 3.13+ |
| Python Library | aio-pika (async) |
| Exchange Type | Topic |
| DLQ | Built-in DLX support |
| Kubernetes | Bitnami Helm chart |

---

## Related ADRs

- ADR-003: Event-Driven Architecture

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |