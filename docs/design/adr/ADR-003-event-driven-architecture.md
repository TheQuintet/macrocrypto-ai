# ADR-003: Event-Driven Architecture

## Status

**Accepted**

---

## Context

We need to choose the communication style between our 4 microservices: synchronous (REST/gRPC) or asynchronous (event-driven).

---

## Decision

**Use Event-Driven Architecture** with RabbitMQ.

---

## Rationale

| Reason | Explanation |
|--------|-------------|
| **Loose Coupling** | Services don't need to know about each other |
| **Scalability** | Services can scale independently |
| **Resilience** | Failures in one service don't affect others |
| **Asynchronous** | Services can process events at their own pace |
| **Event Sourcing** | Events can be stored for audit and replay |

---

## Event Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Event Flow                                         │
│                                                                             │
│  PriceUpdated ──────┐                                                      │
│  IndicatorUpdated ──┼──▶ AI Service ──▶ PredictionGenerated ──▶ API Gateway│
│                     │                                │                     │
│  PriceUpdated ──────┼──▶ Alert Service ◀────────────┘                     │
│  PredictionGenerated │                                                     │
│  AlertAcknowledged ──┘                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **REST/gRPC only** | Tight coupling, synchronous blocking |
| **Webhooks** | Unidirectional, no built-in retry |
| **Polling** | Inefficient, high latency |

---

## Consequences

### Positive

- ✅ Services are decoupled
- ✅ Events can be replayed
- ✅ Natural fit for our domain
- ✅ Supports eventual consistency

### Negative

- ❌ Eventual consistency adds complexity
- ❌ Event ordering must be managed
- ❌ Need to handle duplicate events

---

## Implementation Details

| Component | Technology |
|-----------|------------|
| Broker | RabbitMQ (Topic Exchange) |
| Serialization | JSON |
| Schema Registry | Custom (OpenAPI/JSON Schema) |
| Event Tracking | EventStore or PostgreSQL |

---

## Related ADRs

- ADR-001: Use RabbitMQ
- ADR-002: Database per Service

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |