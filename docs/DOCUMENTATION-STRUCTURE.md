# 📁 MacroCrypto AI - Recommended Documentation Structure

```
macro-crypto-ai/
├── README.md                          # Project overview, quick start
├── LICENSE
├── CONTRIBUTING.md                    # How to contribute
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── docs/                              # PROJECT-SPECIFIC TECH DOCS
│   ├── README.md                      # Docs landing page
│   │
│   ├── architecture/                  # System design docs
│   │   ├── overview.md                # High-level architecture
│   │   ├── event-driven-design.md     # RabbitMQ, events, flow
│   │   ├── data-flow.md               # How data moves through system
│   │   └── diagrams/                  # Architecture diagrams
│   │       ├── system-architecture.png
│   │       └── event-flow.png
│   │
│   ├── services/                      # Per-service documentation
│   │   ├── data-service.md            # Setup, config, endpoints
│   │   ├── ai-service.md              # Prophet model, training
│   │   ├── alert-service.md           # Rule evaluation, notifications
│   │   └── api-gateway.md             # REST API reference
│   │
│   ├── api/                           # API reference (user-facing)
│   │   ├── btc-endpoints.md
│   │   ├── economic-endpoints.md
│   │   ├── forecast-endpoints.md
│   │   └── alert-endpoints.md
│   │
│   ├── guides/                        # How-to guides
│   │   ├── getting-started.md         # Full setup guide (not just quick start)
│   │   ├── local-development.md       # Run locally with Docker
│   │   ├── deployment.md              # Deploy to cloud
│   │   ├── creating-alerts.md         # User guide for alerts
│   │   └── troubleshooting.md
│   │
│   ├── development/                   # Dev team docs (not user-facing)
│   │   ├── setup.md                   # Dev environment setup
│   │   ├── testing.md                 # Unit/integration tests
│   │   ├── ci-cd.md                   # GitHub Actions workflow
│   │   ├── database-migrations.md     # Alembic/PostgreSQL changes
│   │   └── coding-standards.md        # Style guides, conventions
│   │
│   ├── data-models/                   # Database schema docs
│   │   ├── postgres-schema.md
│   │   └── redis-cache-structure.md
│   │
│   ├── events/                        # Event-driven architecture docs
│   │   ├── event-schema.md            # All event types & payloads
│   │   ├── rabbitmq-setup.md          # Exchanges, queues, bindings
│   │   └── dead-letter-queue.md       # For future Phase 2
│   │
│   └── changelog.md                   # Version history
│
├── docker-compose.yml
├── .env.example
└── services/                          # Your actual code
    ├── data-service/
    ├── ai-service/
    ├── alert-service/
    └── api-gateway/
```

---

# 📖 Explanation of This Structure

## 🏠 Root Directory Files

These files live in the project root because **GitHub automatically detects and displays them** prominently. They're the first things visitors see.

| File | Purpose |
|------|---------|
| `README.md` | The front page of your repo. Contains project overview, quick start, badges, and links to deeper docs |
| `LICENSE` | Legal terms for using your code (GitHub shows this in a special banner) |
| `CONTRIBUTING.md` | Guidelines for people who want to contribute (GitHub detects this and links it in PRs) |
| `CODE_OF_CONDUCT.md` | Community behavior rules (GitHub detects this and shows it in your repo) |
| `SECURITY.md` | How to report security issues (GitHub detects this and shows it in the Security tab) |
| `.github/` | Hidden folder containing GitHub-specific files like issue templates and PR templates |

---

## 📂 The `docs/` Directory

This is where all **project-specific technical documentation** lives. These are files that help users and developers understand how to **USE** and **CONTRIBUTE** to your project.

### 📐 `architecture/` - System Design

**Why it's important for MacroCrypto AI:**

Your project is **event-driven** with RabbitMQ and microservices. This folder explains the big picture:

- How services communicate
- Why you chose event-driven architecture
- Data flow from data collection → AI processing → alerts

**Files:**
- `overview.md` - High-level architecture
- `event-driven-design.md` - RabbitMQ, events, flow
- `data-flow.md` - How data moves through system
- `diagrams/` - Architecture diagrams (PNG files)

---

### 🔧 `services/` - Per-Service Documentation

Each of your 3 microservices is complex. This folder documents each one separately:

- **Data Service:** How it collects from CoinGecko, Binance, FRED
- **AI Service:** How Prophet forecasting works
- **Alert Service:** How rules are evaluated
- **API Gateway:** REST endpoints for the dashboard

**Files:**
- `data-service.md` - Setup, config, endpoints
- `ai-service.md` - Prophet model, training
- `alert-service.md` - Rule evaluation, notifications
- `api-gateway.md` - REST API reference

---

### 📡 `api/` - API Reference

This is **user-facing documentation**. If someone wants to build an app on top of your API, they'll look here:

- Which endpoints exist
- Request/response formats
- Authentication requirements (JWT)

**Files:**
- `btc-endpoints.md` - Bitcoin price endpoints
- `economic-endpoints.md` - Economic indicators endpoints
- `forecast-endpoints.md` - AI forecast endpoint
- `alert-endpoints.md` - Alert CRUD endpoints

---

### 📖 `guides/` - How-To Guides

Step-by-step guides for both users and developers:

| File | Audience |
|------|----------|
| `getting-started.md` | Users trying the platform |
| `local-development.md` | Developers setting up locally |
| `deployment.md` | DevOps/developers deploying to cloud |
| `creating-alerts.md` | End users using the dashboard |
| `troubleshooting.md` | Everyone |

---

### 👨‍💻 `development/` - Internal Dev Docs

These are **NOT for users**. They're for your team:

- How to set up the development environment
- How to run tests
- CI/CD pipeline details
- Database migration procedures
- Coding standards and conventions

**Files:**
- `setup.md` - Dev environment setup
- `testing.md` - Unit/integration tests
- `ci-cd.md` - GitHub Actions workflow
- `database-migrations.md` - Alembic/PostgreSQL changes
- `coding-standards.md` - Style guides, conventions

---

### 📊 `data-models/` - Database Schema

Documents what data lives where:

- PostgreSQL tables (users, alerts, prices, economic indicators)
- Redis cache structure

**Files:**
- `postgres-schema.md` - All PostgreSQL tables and relationships
- `redis-cache-structure.md` - Redis keys and data structures

---

### ⚡ `events/` - Event-Driven Architecture

**CRITICAL for MacroCrypto AI!** This documents:

- All event types (`price_update`, `economic_update`, `forecast_event`)
- Event payloads
- RabbitMQ exchanges and queues
- How events flow through the system

**Files:**
- `event-schema.md` - All event types & payloads
- `rabbitmq-setup.md` - Exchanges, queues, bindings
- `dead-letter-queue.md` - For future Phase 2

---

### 📝 `changelog.md` - Version History

Tracks what changed in each release. Important for users upgrading.

---

## 🐳 Infrastructure Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Defines all services (PostgreSQL, Redis, RabbitMQ, 3 microservices) |
| `.env.example` | Example environment variables. Copy to `.env` and fill in |

---

## 💻 The `services/` Directory

This is where your **actual code** lives. Each service is its own subproject with its own:

- `Dockerfile`
- `requirements.txt` (Python dependencies)
- Source code
- Tests

```
services/
├── data-service/    # Data collection from CoinGecko, Binance, FRED
├── ai-service/      # Prophet forecasting model
├── alert-service/   # Rule evaluation and email notifications
└── api-gateway/     # REST API endpoints
```

---

## 🎯 The Golden Rule

> **Root** = Project Meta (README, LICENSE, CONTRIBUTING)
>
> **`docs/`** = Everything about using and understanding the project
>
> **`services/`** = The actual code

---

## ✅ Why This Works for MacroCrypto AI

| Your Project Aspect | Where It's Documented |
|---------------------|----------------------|
| "What is this?" | Root `README.md` |
| "How do I run it?" | `docs/guides/local-development.md` |
| "How does event-driven architecture work?" | `docs/architecture/event-driven-design.md` |
| "What events exist?" | `docs/events/event-schema.md` |
| "How do I call the API?" | `docs/api/` |
| "How do I contribute?" | Root `CONTRIBUTING.md` |
| "How do I test my changes?" | `docs/development/testing.md` |
| "What data is stored?" | `docs/data-models/` |
| "What changed in v1.0?" | `docs/changelog.md` |

---
