# Software Design & Architecture Plan — MacroCrypto AI

This document provides a practical, prioritized plan for the software design and architecture of MacroCrypto AI. It covers what we need to produce, what we can simplify, and what we can skip for the MVP — based on our 3-month timeline, 5-person team, and 17 user stories.

---

## 1. What We Already Have

Before starting the design phase, we already have:

| Item | Status |
|------|--------|
| Project Scope | ✅ Defined |
| Team Roles (5) | ✅ Assigned |
| User Personas (3) | ✅ Created |
| User Stories (17) | ✅ Written and prioritized |
| Sub-Issues (~279) | ✅ Defined |
| Epics (9) | ✅ Created |
| Milestones / Sprints | ✅ Defined/Planned ahead of each meeting |
| GitHub Projects | ✅ Set up |

We are now entering the **analysis → design → architecture** phase.

---

## 2. Recommended Design Phases

The following phases should be completed **before** starting Sprint 1. They provide the foundation for consistent development.

---

### Phase 1: Requirements Analysis (✅ Almost Done)

| Deliverable | Status |
|-------------|--------|
| Prioritized backlog | ✅ Complete |
| Acceptance criteria | ✅ Complete (in each user story) |
| Story dependencies | ✅ Complete |
| Business rules | ⚠️ Needs documenting |

**What to do next:**
- Document business rules (e.g., alert thresholds, trading recommendation logic, correlation strength thresholds, regime classification rules)
- Store in `docs/business-rules.md`

---

### Phase 2: Domain-Driven Design (Simplified)

**Do these:**
- **Ubiquitous Language** — Create a glossary of domain terms (BTC, Prediction, Confidence Interval, Alert, Correlation, Regime, Macro Indicator, etc.)
- **Domain Model** — Identify Entities, Value Objects, Aggregates, and Domain Events
- **Event Storming (lightweight)** — Map key domain events and commands for the core flows

**Skip:**
- Full formal Event Storming workshop (do as a team discussion instead)
- Heavy context mapping (our 4 microservices are already defined)

**Deliverables:**
- `docs/ubiquitous-language.md`
- `docs/domain-model.md`

---

### Phase 3: Microservice Design

Our 4 microservices are already defined. For each service, we need to document:

| Service | Responsibilities | Owned Data | Events Produced | Events Consumed | APIs |
|---------|------------------|------------|-----------------|-----------------|------|
| Data Ingestion Service | Collect BTC + macro data | TimescaleDB, PostgreSQL | PriceUpdated, IndicatorUpdated | — | Internal |
| AI Service | Run ML models, generate predictions | TimescaleDB, MLflow | PredictionGenerated | PriceUpdated | Internal |
| API Gateway | REST endpoints, auth, rate limiting | PostgreSQL (users) | — | PredictionGenerated | External |
| Alert Service | Evaluate rules, send notifications | PostgreSQL | AlertTriggered | PriceUpdated, PredictionGenerated, IndicatorUpdated | Internal |

**Deliverables:**
- `docs/microservices.md`

---

### Phase 4: Event-Driven Architecture

| Deliverable | Description |
|-------------|-------------|
| **Event Catalog** | List all domain events (e.g., PriceUpdated, PredictionGenerated, AlertTriggered, IndicatorUpdated) |
| **Commands Catalog** | List all commands (e.g., FetchPrice, GeneratePrediction, CreateAlert, SendNotification) |
| **Broker Design** | Topic/queue structure for RabbitMQ |
| **Event Flow Diagrams** | Visuals showing event flow between services |

**What to produce:**
- `docs/event-catalog.md`
- `docs/commands-catalog.md`
- `docs/event-flow-diagrams.md` (simple diagrams)

---

### Phase 5: Architecture Documentation

| Deliverable | Description |
|-------------|-------------|
| **C4 Model** | Context, Container, and Component diagrams |
| **API Design** | REST endpoints, OpenAPI specification, authentication |
| **Event Contracts** | JSON schemas for each event |
| **Data Model** | ER diagrams, TimescaleDB and PostgreSQL schemas |

**What to produce:**
- `docs/c4-model.md`
- `docs/api-design.md` (OpenAPI)
- `docs/event-contracts.md`
- `docs/data-model.md`

---

### Phase 6: Cross-Cutting Concerns

| Concern | Implementation | Document |
|---------|----------------|----------|
| Authentication | JWT, OAuth2, RBAC | `docs/auth.md` |
| Observability | Logging (ELK), Metrics (Prometheus/Grafana), Tracing | `docs/observability.md` |
| Fault Tolerance | Retry, Circuit Breaker, Dead Letter Queue, Timeouts | `docs/fault-tolerance.md` |
| Scalability | Horizontal scaling, Redis caching, load balancing | `docs/scalability.md` |

---

### Phase 7: ADRs & NFRs

| Deliverable | Description |
|-------------|-------------|
| **ADRs (Architecture Decision Records)** | Document key decisions (e.g., "Use RabbitMQ over Kafka", "Database per service") |
| **Non-Functional Requirements** | Performance, availability, security, latency targets |
| **Traceability Matrix (simplified)** | Map requirements to services and APIs |

**What to produce:**
- `docs/adr/ADR-001-use-rabbitmq.md`
- `docs/adr/ADR-002-database-per-service.md`
- `docs/adr/ADR-003-event-driven-architecture.md`
- `docs/non-functional-requirements.md`

---

## 3. UML Modeling — Selective Approach

We should **not** do all UML diagrams. Focus on the most valuable ones:

| Diagram | Priority | Reason |
|---------|----------|--------|
| **Domain Class Diagram** | ✅ High | Shows entities and relationships |
| **Sequence Diagrams** | ✅ High | Show API flows (3-4 key user stories) |
| **Component Diagram** | ✅ High | Shows service boundaries |
| **State Machine Diagrams** | ✅ Medium | For Alerts, Predictions, Data Ingestion |
| **Deployment Diagram** | ✅ Medium | Shows infrastructure |
| Use Case Diagram | ❌ Skip | User stories already cover this |
| Activity Diagrams | ⚠️ Optional | Helpful but time-consuming |
| Package Diagram | ❌ Skip | Not needed for microservices |

**What to produce:**
- `docs/uml/domain-class-diagram.png`
- `docs/uml/sequence-diagrams.md`
- `docs/uml/component-diagram.png`
- `docs/uml/state-machine-diagrams.md`
- `docs/uml/deployment-diagram.png`

---

## 4. What to Skip for MVP

| Item | Reason |
|------|--------|
| **CQRS** | Adds complexity without clear benefit for our use case |
| **Full UML (all 8 diagrams)** | Too time-consuming; focus on 3-4 key diagrams |
| **Full Event Storming** | Good but can be simplified |
| **Full Traceability Matrix** | Time-consuming; simplified version is sufficient |
| **Formal Context Mapping** | Not needed with 4 well-defined services |

---

## 5. Priority Summary

| Priority | Phase | Deliverables |
|----------|-------|--------------|
| **P0** | Phase 1-5 | Requirements, DDD, Microservices, Event-Driven, Architecture |
| **P0** | Phase 6 | Cross-Cutting Concerns |
| **P0** | Phase 7 | ADRs & NFRs |
| **P1** | UML | Domain Class, Sequence (3-4), Component, State Machine, Deployment |
| **P2** | Optional | Activity Diagrams, additional Sequence Diagrams |

---

## 6. Recommended Epic Structure for GitHub

Create these epics in GitHub to track the design work:

| Epic | Deliverables |
|------|--------------|
| **Epic: Requirements & Business Rules** | Business rules document |
| **Epic: Domain-Driven Design** | Ubiquitous language, domain model, event storming output |
| **Epic: Microservice Design** | Service catalog, responsibilities, database per service |
| **Epic: Event-Driven Architecture** | Event catalog, commands, broker design, event flows |
| **Epic: Architecture & API** | C4 model, API design, event contracts, data model |
| **Epic: Cross-Cutting Concerns** | Auth, observability, fault tolerance, scalability |
| **Epic: ADRs & NFRs** | ADRs, performance/availability targets |
| **Epic: UML Modeling** | Domain class, sequence, state machine, component, deployment diagrams |

---

## 7. Documents to Produce

```
docs/
├── business-rules.md
├── ubiquitous-language.md
├── domain-model.md
├── microservices.md
├── event-catalog.md
├── commands-catalog.md
├── event-flow-diagrams.md
├── c4-model.md
├── api-design.md
├── event-contracts.md
├── data-model.md
├── auth.md
├── observability.md
├── fault-tolerance.md
├── scalability.md
├── non-functional-requirements.md
├── adr/
│   ├── ADR-001-use-rabbitmq.md
│   ├── ADR-002-database-per-service.md
│   └── ADR-003-event-driven-architecture.md
└── uml/
    ├── domain-class-diagram.png
    ├── sequence-diagrams.md
    ├── component-diagram.png
    ├── state-machine-diagrams.md
    └── deployment-diagram.png
```
