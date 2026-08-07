# Non-Functional Requirements — MacroCrypto AI

This document defines the non-functional requirements for the MacroCrypto AI platform.

---

## 1. Performance

| Requirement | Target | Description |
|-------------|--------|-------------|
| **API Response Time** | < 200ms (cached), < 500ms (uncached) | 95th percentile |
| **Event Processing Latency** | < 100ms | Time from event publish to processing |
| **Prediction Generation** | < 5s | Prophet model training and prediction |
| **BTC Price Freshness** | < 5 seconds | Real-time WebSocket updates |
| **Indicator Freshness** | < 24 hours | Daily scheduled updates |
| **Concurrent Users** | 1,000+ | Simultaneous active users |

---

## 2. Availability

| Requirement | Target | Description |
|-------------|--------|-------------|
| **System Uptime** | 99.5% | Monthly uptime (excluding planned maintenance) |
| **Planned Maintenance** | < 4 hours/month | Scheduled downtime window |
| **Recovery Time (RTO)** | < 1 hour | Time to restore service after failure |
| **Recovery Point (RPO)** | < 1 hour | Maximum data loss acceptable |

---

## 3. Security

| Requirement | Target | Description |
|-------------|--------|-------------|
| **Authentication** | JWT | Access token: 15 min, Refresh token: 7 days |
| **Password Storage** | bcrypt | 12 salt rounds |
| **Data Encryption** | TLS 1.2+ | In transit |
| **Data Encryption** | AES-256 | At rest |
| **API Rate Limiting** | 100/min (user) | By user type |
| **CORS** | Restricted | Only allowed origins |

---

## 4. Scalability

| Requirement | Target | Description |
|-------------|--------|-------------|
| **Horizontal Scaling** | All services | Stateless design |
| **Auto-Scaling** | 70% CPU | Kubernetes HPA |
| **Database Scaling** | TimescaleDB hypertables, read replicas | PostgreSQL |
| **Cache Scaling** | Redis Cluster | For predictions and API responses |

---

## 5. Reliability

| Requirement | Target | Description |
|-------------|--------|-------------|
| **Retry Mechanism** | 3 retries | Exponential backoff |
| **Circuit Breaker** | 5 failures | Open state for 60 seconds |
| **Dead Letter Queue** | Enabled | Failed messages stored for 7 days |
| **Health Checks** | Every 30 seconds | /health endpoint on each service |

---

## 6. Data Quality

| Requirement | Target | Description |
|-------------|--------|-------------|
| **Price Accuracy** | ±0.01% | Compared to market price |
| **Prediction Accuracy** | < 5% MAE | Mean Absolute Error |
| **Data Completeness** | > 95% | Missing data threshold |
| **Data Freshness Alert** | 48 hours | Alert if no new data |

---

## 7. Compliance

| Requirement | Target | Description |
|-------------|--------|-------------|
| **GDPR** | Compliant | For EU users |
| **CCPA** | Compliant | For California users |
| **Data Retention** | 30 days (logs) | Configurable per data type |
| **Data Deletion** | 30 days | After user deletion request |

---

## 8. Monitoring

| Requirement | Target | Description |
|-------------|--------|-------------|
| **Logging** | ELK Stack | Centralized logging |
| **Metrics** | Prometheus + Grafana | System and business metrics |
| **Tracing** | OpenTelemetry | Distributed tracing |
| **Alerts** | PagerDuty / Slack | On-call notifications |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |