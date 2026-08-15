# Alert Service

MacroCrypto AI Alert Service - Evaluate alert conditions and deliver notifications.

## Overview

The Alert Service is responsible for:
- Evaluating alert rules based on BTC price and economic indicator data
- Sending notifications (in-app + email) when alert conditions are met
- Managing alert lifecycle (active → triggered → dismissed/archived)

## Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | REST API for alert management |
| Database | PostgreSQL | Alert rules, history, user preferences |
| Cache | Redis | Rate limiting, alert cooldowns |
| Message Broker | RabbitMQ | Event consumption and production |
| Notifications | SMTP/SendGrid | Email delivery |

## Events

### Consumed Events

| Event | Source | Description |
|-------|--------|-------------|
| `PriceUpdated` | Data Service | New BTC price available |
| `IndicatorUpdated` | Data Service | New economic indicator available |

### Produced Events

| Event | Destination | Description |
|-------|-------------|-------------|
| `AlertTriggered` | API Gateway | Alert condition met |

## Quick Start

### Prerequisites
- Python 3.13.14
- PostgreSQL (via Docker or local)
- Redis (via Docker or local)
- RabbitMQ (via Docker or local)

### Local Development (Without Docker)

```bash
# Navigate to alert-service directory
cd ~/GitHub\ Repos/macrocrypto-ai/services/alert-service

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment variables
cp .env.example .env

# Edit .env for local development
# Change DATABASE_URL, REDIS_HOST, RABBITMQ_HOST to localhost

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

### Local Development (With Docker)

```bash
# From the project root
cd ~/GitHub\ Repos/macrocrypto-ai

# Start all infrastructure services (postgres, redis, rabbitmq)
docker compose up -d postgres redis rabbitmq

# Start alert-service
docker compose up -d alert-service

# View logs
docker compose logs -f alert-service
```

### Using Make Commands

```bash
# From the project root
make alert-up          # Start alert-service
make alert-down        # Stop alert-service
make alert-logs        # View logs
make alert-restart     # Restart alert-service
make alert-shell       # Open shell in container
```

## API Endpoints

### Alert Management (REST API)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/alerts` | Create a new alert |
| GET | `/api/v1/alerts` | List all alerts for a user |
| GET | `/api/v1/alerts/{id}` | Get alert by ID |
| PUT | `/api/v1/alerts/{id}` | Update an alert |
| DELETE | `/api/v1/alerts/{id}` | Delete (archive) an alert |
| POST | `/api/v1/alerts/{id}/disable` | Disable an alert |
| POST | `/api/v1/alerts/{id}/dismiss` | Dismiss a triggered alert |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications` | Get user notifications |
| POST | `/api/v1/notifications/{id}/read` | Mark notification as read |
| POST | `/api/v1/notifications/read-all` | Mark all as read |

### Health Checks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/ready` | Readiness check |

## Alert Types

### 1. Price Alerts

- **Reaches**: BTC reaches a specific price
- **Crosses Above**: BTC crosses above a threshold
- **Crosses Below**: BTC crosses below a threshold

Example:
```json
{
  "alert_type": "price",
  "config": {
    "asset": "BTC/USD",
    "threshold": 100000,
    "condition": "crosses_above"
  }
}
```

### 2. Prediction Change Alerts

- **Prediction Change**: Prediction changes by X%
- **Confidence Change**: Confidence changes by X%

Example:
```json
{
  "alert_type": "prediction_change",
  "config": {
    "threshold_percent": 2.0,
    "direction": "both"
  }
}
```

### 3. Macro Event Alerts

- **Event Reminder**: X hours before major economic events

Example:
```json
{
  "alert_type": "macro_event",
  "config": {
    "event_types": ["FOMC", "CPI"],
    "timeframes": ["24h", "12h", "1h"]
  }
}
```

## Alert Lifecycle

```
Active → Triggered → Dismissed/Archived
Active → Disabled (user disables)
Active → Expired (one-time alerts)
```

## Testing

### Run All Tests

```bash
# From project root
make alert-test

# Or from alert-service directory
pytest tests/ -v
```

### Run Specific Test Types

```bash
# Unit tests only
make alert-test-unit
pytest tests/unit/ -v

# Integration tests only
make alert-test-int
pytest tests/integration/ -v

# With coverage
make alert-test-cov
pytest tests/ --cov=app --cov-report=html
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service identifier | `alert-service` |
| `SERVICE_PORT` | Port to listen on | `8003` |
| `LOG_LEVEL` | Log level | `INFO` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_HOST` | Redis host | `redis` |
| `RABBITMQ_HOST` | RabbitMQ host | `rabbitmq` |
| `EMAIL_ENABLED` | Enable email notifications | `false` |
| `MAX_ALERTS_PER_USER` | Max alerts per user | `50` |
| `ALERT_RETENTION_DAYS` | Alert history retention | `30` |

See `.env.example` for all available variables.

## Project Structure

```
alert-service/
├── app/
│   ├── api/              # REST API routes
│   ├── cache/            # Redis client
│   ├── database/         # PostgreSQL session
│   ├── messaging/        # RabbitMQ consumer/producer
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utilities
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── Dockerfile            # Container build
└── .env.example          # Environment template
```

## Troubleshooting

### Redis Connection Failed

```bash
# Check if Redis is running
docker compose ps redis
# Or locally
redis-cli ping
```

### RabbitMQ Connection Failed

```bash
# Check RabbitMQ status
docker compose ps rabbitmq
# Or check management UI
open http://localhost:15672
```

### Database Connection Failed

```bash
# Check PostgreSQL
docker compose ps postgres
# Or connect directly
psql -U macro -d macrocrypto -h localhost
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `make alert-test`
4. Format code: `make alert-format`
5. Create a pull request

## License

Proprietary - MacroCrypto AI