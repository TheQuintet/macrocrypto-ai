# ADR-002: Database per Service

## Status

**Accepted**

---

## Context

We have 4 microservices that need to store data. We need to decide whether to use a shared database or give each service its own database.

---

## Decision

**Use Database per Service** (one database per microservice).

---

## Rationale

| Reason | Explanation |
|--------|-------------|
| **Loose Coupling** | Services are independent and can evolve separately |
| **Data Ownership** | Each service owns its data |
| **Scalability** | Databases can be scaled independently |
| **Technology Choice** | Each service can choose the right database type |
| **Failure Isolation** | One service's database failure doesn't affect others |

---

## Database Allocation

| Service | Database | Purpose |
|---------|----------|---------|
| Data Ingestion | TimescaleDB | BTC prices, macro indicators |
| Data Ingestion | Redis | Current price cache |
| AI Service | TimescaleDB | Predictions |
| AI Service | Redis | Prediction cache |
| AI Service | MLflow | Model registry |
| API Gateway | PostgreSQL | Users, API keys, export history |
| Alert Service | PostgreSQL | Alerts, notifications, history |

---

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Shared Database** | Tight coupling, single point of failure, difficult to scale |
| **Shared Schema** | Still coupling, ownership unclear |

---

## Consequences

### Positive

- ✅ Services are independent
- ✅ Can choose optimal database per service
- ✅ Can scale databases independently

### Negative

- ❌ More databases to manage
- ❌ Data consistency across services requires event-driven approach
- ❌ More DevOps complexity

---

## Implementation Details

| Component | Technology |
|-----------|------------|
| TimescaleDB | 2.16+ (hypertables, continuous aggregates) |
| PostgreSQL | 15+ (JSONB, indexing) |
| Redis | 7.2+ (caching) |
| MLflow | 2.9+ (model registry) |

---

## Related ADRs

- ADR-003: Event-Driven Architecture

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |