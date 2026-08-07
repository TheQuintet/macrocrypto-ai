# Cross-Cutting Concerns — MacroCrypto AI

This document defines the cross-cutting concerns for the MacroCrypto AI platform, including authentication, observability, fault tolerance, and scalability.

---

## 1. Authentication

### 1.1 Overview

The platform uses **JWT (JSON Web Tokens)** for authentication and authorization.

| Component | Technology |
|-----------|------------|
| Token Format | JWT (JSON Web Token) |
| Algorithm | HS256 or RS256 |
| Expiration | Access: 15 minutes, Refresh: 7 days |
| Storage | HTTP-only secure cookies (recommended) or Authorization header |

---

### 1.2 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Authentication Flow                                │
│                                                                             │
│  ┌──────────┐                                                              │
│  │  User    │                                                              │
│  └────┬─────┘                                                              │
│       │                                                                    │
│       │ 1. POST /auth/login (email, password)                             │
│       ▼                                                                    │
│  ┌──────────────┐                                                         │
│  │ API Gateway  │                                                         │
│  └──────┬───────┘                                                         │
│         │                                                                  │
│         │ 2. Validate credentials                                         │
│         │ 3. Generate JWT tokens                                          │
│         │ 4. Return access_token + refresh_token                          │
│         ▼                                                                  │
│  ┌──────────┐                                                              │
│  │  User    │                                                              │
│  └────┬─────┘                                                              │
│       │                                                                    │
│       │ 5. Access protected endpoint with access_token                    │
│       ▼                                                                    │
│  ┌──────────────┐                                                         │
│  │ API Gateway  │                                                         │
│  └──────┬───────┘                                                         │
│         │                                                                  │
│         │ 6. Validate JWT signature and expiration                        │
│         │ 7. Check user permissions                                        │
│         │ 8. Process request                                              │
│         ▼                                                                  │
│  ┌──────────┐                                                              │
│  │ Response │                                                              │
│  └──────────┘                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.3 JWT Token Structure

**Access Token Payload:**

```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "userType": "REGISTERED",
  "iat": 1691234567,
  "exp": 1691235467
}
```

### 1.4 Refresh Token Flow

| Step | Description |
|------|-------------|
| 1 | Access token expires after 15 minutes |
| 2 | User sends refresh_token to `/auth/refresh` |
| 3 | API Gateway validates refresh token |
| 4 | New access token generated |
| 5 | User receives new access token |

### 1.5 Password Hashing

| Component | Specification |
|-----------|---------------|
| Algorithm | bcrypt |
| Salt Rounds | 12 |
| Storage | Hashed in PostgreSQL |

### 1.6 Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| **Guest** | View public data only |
| **Registered User** | View all data, create alerts, export data |
| **Admin** | All permissions + user management |

### 1.7 Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| Strict-Transport-Security | max-age=31536000 | Enforce HTTPS |
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| Content-Security-Policy | default-src 'self' | Restrict resource loading |

---

## 2. Observability

### 2.1 Overview

Observability is implemented through **logging**, **metrics**, and **tracing**.

| Component | Technology |
|-----------|------------|
| Logging | ELK Stack (Elasticsearch, Logstash, Kibana) |
| Metrics | Prometheus + Grafana |
| Tracing | OpenTelemetry / Jaeger |
| Health Checks | `/health` endpoint on each service |

---

### 2.2 Logging

**Log Levels:**

| Level | Use Case |
|-------|----------|
| **ERROR** | Errors that prevent normal operation |
| **WARN** | Warnings that may lead to errors |
| **INFO** | Important events (user login, alert triggered) |
| **DEBUG** | Detailed debugging information (development only) |

**Log Format (JSON):**

```json
{
  "timestamp": "2026-08-07T10:30:00Z",
  "level": "INFO",
  "service": "api-gateway",
  "correlation_id": "abc-123-def-456",
  "user_id": "user-123",
  "endpoint": "/api/v1/predict/btc",
  "method": "GET",
  "status": 200,
  "response_time_ms": 150,
  "message": "Prediction endpoint called"
}
```

**Log Storage:**

| Component | Retention |
|-----------|-----------|
| Elasticsearch | 30 days |
| Logstash | Pipeline processing |
| Kibana | Visualization and querying |

---

### 2.3 Metrics

**Key Metrics:**

| Metric Type | Example Metrics |
|-------------|-----------------|
| **Request** | Request count, latency, error rate |
| **Business** | Predictions generated, alerts triggered, users registered |
| **System** | CPU usage, memory usage, database connections |
| **Event** | Event published count, event consumer lag |

**Prometheus Metrics:**

```yaml
# Request metrics
http_requests_total{endpoint="/predict/btc", method="GET", status="200"}
http_request_duration_seconds{endpoint="/predict/btc"}

# Business metrics
predictions_generated_total{horizon="24h"}
alerts_triggered_total{alert_type="price"}

# System metrics
cpu_usage_percent
memory_usage_bytes
database_connections_active
```

**Grafana Dashboards:**

| Dashboard | Purpose |
|-----------|---------|
| **System Health** | CPU, memory, service status |
| **API Performance** | Request rate, latency, error rate |
| **Business Metrics** | Predictions, alerts, user activity |
| **Event Pipeline** | Event throughput, consumer lag |

---

### 2.4 Tracing

**Trace Sampling:**

| Environment | Sampling Rate |
|-------------|---------------|
| Development | 100% |
| Staging | 50% |
| Production | 5% |

**Trace Attributes:**

| Attribute | Value |
|-----------|-------|
| service.name | api-gateway, ai-service, etc. |
| http.method | GET, POST, etc. |
| http.url | /api/v1/predict/btc |
| http.status_code | 200, 400, 500 |

---

### 2.5 Health Checks

| Service | Endpoint | Check |
|---------|----------|-------|
| API Gateway | `/health` | Database, Redis, RabbitMQ |
| AI Service | `/health` | Database, MLflow, Redis |
| Data Ingestion | `/health` | Database, Redis, External APIs |
| Alert Service | `/health` | Database, RabbitMQ, Email |

---

## 3. Fault Tolerance

### 3.1 Overview

The platform implements fault tolerance through **retries**, **circuit breakers**, **dead letter queues**, and **timeouts**.

---

### 3.2 Retry Strategy

| Parameter | Default Value |
|-----------|---------------|
| Max Retries | 3 |
| Initial Delay | 1 second |
| Backoff Type | Exponential (2x) |
| Max Delay | 60 seconds |

**Retry Conditions:**

| Condition | Retry? |
|-----------|--------|
| Connection timeout | ✅ Yes |
| Rate limit (429) | ✅ Yes |
| 5xx error | ✅ Yes |
| 4xx error (validation) | ❌ No |
| 404 Not Found | ❌ No |

---

### 3.3 Circuit Breaker

| Parameter | Default Value |
|-----------|---------------|
| Failure Threshold | 5 failures |
| Success Threshold | 3 successes |
| Open State Wait | 60 seconds |

**Circuit Breaker States:**

```
┌─────────────┐
│   CLOSED    │ ← Normal operation (requests flow)
└──────┬──────┘
       │
       │ 5 failures
       ▼
┌─────────────┐
│    OPEN     │ ← All requests fail fast
└──────┬──────┘
       │
       │ 60 seconds
       ▼
┌─────────────┐
│  HALF-OPEN  │ ← Test with limited requests
└──────┬──────┘
       │
       │ 3 successes → CLOSED
       │ 1 failure   → OPEN
```

---

### 3.4 Dead Letter Queue (DLQ)

| Parameter | Value |
|-----------|-------|
| DLQ Name | `macro-crypto-dlq` |
| Retention | 7 days |
| Alert Threshold | > 10 messages |

**DLQ Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Dead Letter Queue Flow                             │
│                                                                             │
│  ┌──────────────┐                                                          │
│  │   Message    │                                                          │
│  │   Published  │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                  │
│         ▼                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │   Exchange   │────▶│    Queue     │────▶│   Consumer   │              │
│  └──────────────┘     └──────┬───────┘     └──────┬───────┘              │
│                              │                    │                       │
│                              │                    │ Failure (x3 retries)  │
│                              ▼                    ▼                       │
│                      ┌──────────────┐     ┌──────────────┐              │
│                      │   DLQ        │     │   Log Error  │              │
│                      │   Exchange   │     │   Alert Team │              │
│                      └──────────────┘     └──────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.5 Timeouts

| Service / Operation | Timeout |
|---------------------|---------|
| Data Ingestion (API calls) | 30 seconds |
| AI Service (Prediction) | 60 seconds |
| Alert Service (Email) | 10 seconds |
| API Gateway (External) | 30 seconds |
| Database Queries | 5 seconds |
| Service-to-Service Calls | 10 seconds |

---

### 3.6 Circuit Breaker Targets

| Service | Circuit Breaker | Threshold |
|---------|-----------------|-----------|
| Data Ingestion → CoinGecko | ✅ | 5 failures |
| Data Ingestion → FRED | ✅ | 5 failures |
| AI Service → MLflow | ✅ | 5 failures |
| Alert Service → Email | ✅ | 5 failures |
| API Gateway → Database | ✅ | 5 failures |

---

## 4. Scalability

### 4.1 Overview

The platform achieves scalability through **horizontal scaling**, **caching**, and **load balancing**.

---

### 4.2 Horizontal Scaling

| Service | Scaling Strategy | Stateless? |
|---------|------------------|------------|
| API Gateway | Horizontal (based on CPU/request count) | ✅ Yes |
| AI Service | Horizontal (based on CPU) | ✅ Yes |
| Data Ingestion | Horizontal (based on CPU) | ✅ Yes |
| Alert Service | Horizontal (based on CPU) | ✅ Yes |

**Kubernetes Horizontal Pod Autoscaler (HPA):**

| Service | Metric | Target |
|---------|--------|--------|
| API Gateway | CPU | 70% |
| AI Service | CPU | 70% |
| Data Ingestion | CPU | 70% |
| Alert Service | CPU | 70% |

---

### 4.3 Caching Strategy

| Cache Level | Technology | Purpose | TTL |
|-------------|------------|---------|-----|
| Service-level | Redis | Predictions, API responses | 5 min |
| API-level | Redis | REST API responses | 5 min |
| Database-level | TimescaleDB | Query optimization | N/A |

**Cache Layers:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Caching Strategy                                   │
│                                                                             │
│  ┌──────────────┐         ┌──────────────┐                                │
│  │   Client     │─────▶   │   API        │                                │
│  │              │         │   Gateway    │                                │
│  └──────────────┘         └──────┬───────┘                                │
│                                   │                                        │
│                                   │ 1. Check cache                        │
│                                   ▼                                        │
│                            ┌──────────────┐                               │
│                            │   Redis      │                               │
│                            │   (Cache)    │                               │
│                            └──────┬───────┘                               │
│                                   │                                        │
│                                   │ 2. Cache miss                         │
│                                   ▼                                        │
│                            ┌──────────────┐                               │
│                            │   Service    │                               │
│                            │              │                               │
│                            └──────┬───────┘                               │
│                                   │                                        │
│                                   │ 3. Store in cache                    │
│                                   ▼                                        │
│                            ┌──────────────┐                               │
│                            │   Redis      │                               │
│                            │   (Cache)    │                               │
│                            └──────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.4 Load Balancing

| Level | Technology | Purpose |
|-------|------------|---------|
| Ingress | Nginx / Kubernetes Ingress | External traffic distribution |
| Service | Kubernetes Service | Internal load balancing |
| Database | Read replicas | Query distribution |

---

### 4.5 Database Scaling

| Database | Scaling Strategy |
|----------|------------------|
| TimescaleDB | Hypertables, continuous aggregates |
| PostgreSQL | Read replicas, connection pooling |
| Redis | Redis Cluster |

---

### 4.6 Performance Targets

| Metric | Target |
|--------|--------|
| API Response (cached) | < 200ms |
| API Response (non-cached) | < 500ms |
| Event Processing | < 100ms |
| Prediction Generation | < 5s |
| Database Query | < 100ms |
| System Uptime | 99.5% |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — all sections complete |