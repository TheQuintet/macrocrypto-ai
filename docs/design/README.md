# System Design and Architecture

## Overview

This directory contains the design and architecture documentation for the MacroCrypto AI platform. It describes the system structure, service responsibilities, API design, data model, business rules, architectural decisions, and supporting UML diagrams.

The documentation serves as a reference for understanding the system, maintaining the implementation, reviewing design decisions, and guiding future development.

## Documentation Structure

### 1. System Architecture

Documents describing the overall system structure, architectural organization, and communication between components.

- [C4 Model](c4-model.md) — System architecture and component relationships using the C4 model.
- [Event-Driven Architecture](event-driven-architecture.md) — Event-driven communication, messaging flows, and interactions between services.
- [Cross-Cutting Concerns](cross-cutting-concerns.md) — Shared technical concerns such as security, logging, error handling, and reliability.
- [Architectural and Object-Oriented Patterns](architectural-object-oriented-patterns.md) — Design patterns used in the system and their implementation rationale.
- [Non-Functional Requirements](non-functional-requirements.md) — Quality attributes and operational requirements for the platform.

### 2. API and Data Design

Documents describing external interfaces, data structures, and persistence.

- [API Design](api-design.md) — API endpoints, request and response structures, and interface conventions.
- [Database Design](database-design.md) — Database structure, data relationships, and persistence considerations.

### 3. Domain and Business Design

Documents defining the business concepts, rules, and terminology used throughout the platform.

- [Domain Model](domain-model.md) — Core domain concepts, entities, relationships, and domain boundaries.
- [Business Rules](business-rules.md) — Business logic, validation rules, and system constraints.
- [Ubiquitous Language](ubiquitous-language.md) — Shared terminology used across the domain, implementation, and documentation.

### 4. AI and Feature Engineering

Documents supporting the AI service and its data preparation processes.

- [Feature Engineering Guide](ai-service/feature-engineering-guide.md) — Feature definitions, data preparation, and feature engineering considerations for model development.

### 5. Architecture Decision Records (ADRs)

The [`adr/`](adr/) directory contains records documenting selected architectural decisions and their rationale.

- [ADR-001: Use RabbitMQ](adr/ADR-001-use-rabbitmq.md)
- [ADR-002: Database per Service](adr/ADR-002-database-per-service.md)
- [ADR-003: Event-Driven Architecture](adr/ADR-003-event-driven-architecture.md)
- [ADR-004: Use Prophet](adr/ADR-004-use-prophet.md)
- [ADR-005: Use FastAPI](adr/ADR-005-use-fastapi.md)

### 6. UML Diagrams

The [`uml/`](uml/) directory contains visual representations of the system design.

- [UML Documentation](uml/README.md) — Index of available UML diagrams.
- [Class Diagram](uml/class-diagram/class-diagram.svg) — Visual representation of classes and their relationships.
- [Sequence Diagram](uml/sequence-diagram/sequence-diagram.svg) — Visual representation of interactions between system components over time.