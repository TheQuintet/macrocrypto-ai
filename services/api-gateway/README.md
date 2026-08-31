```markdown
# API Gateway Service

MacroCrypto AI API Gateway - REST API gateway for internal microservices.

## Overview

The API Gateway is the entry point for all client requests. It routes requests to internal microservices, handles authentication, rate limiting, request/response transformation, and real-time WebSocket updates.

## Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | REST API entry point |
| Cache | Redis | Session management, rate limiting, caching |
| Message Broker | RabbitMQ | Event consumption/production |
| Service Calls | HTTPX | Internal service communication |
| WebSocket | FastAPI | Real-time price updates |

## Services

| Service | Port | URL |
|---------|------|-----|
| Data Service | 8001 | `http://data-service:8001` |
| AI Service | 8002 | `http://ai-service:8002` |
| Alert Service | 8003 | `http://alert-service:8003` |
| API Gateway | 8000 | `http://api-gateway:8000` |

## Quick Start

### Prerequisites
- Python 3.13.14
- Redis
- RabbitMQ
- PostgreSQL

### Local Development (Without Docker)

```bash
# Navigate to api-gateway directory
cd ~/GitHub\ Repos/macrocrypto-ai/services/api-gateway

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment variables
cp .env.example .env

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get tokens |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/auth/logout` | POST | Logout |
| `/api/v1/auth/change-password` | POST | Change password |
| `/api/v1/auth/verify` | GET | Verify email |

### Predictions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/predict/btc` | GET | BTC predictions (24h/7d) |
| `/api/v1/predict/btc/accuracy` | GET | Prediction accuracy metrics |

### Market Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/btc/prices` | GET | Historical BTC prices |
| `/api/v1/indicators` | GET | Macroeconomic indicators |
| `/api/v1/correlation/btc` | GET | BTC-macro correlation |
| `/api/v1/regimes/btc` | GET | Market regime data |

### Recommendations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recommendations/btc` | GET | Trade recommendations |

## WebSocket

### Real-Time Price Updates

Connect to receive real-time BTC price updates and alerts.

**Endpoint:** `ws://localhost:8000/ws`

**Optional Query Parameter:**
- `token`: JWT access token (for authenticated connections)

**Example Connection:**
```bash
# Using wscat (requires Node.js)
wscat -c "ws://localhost:8000/ws"

# With authentication
wscat -c "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"
```

**Message Format (Server → Client):**
```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTC",
    "price": 45000.00,
    "change_24h_percent": 2.5,
    "volume": 1500000,
    "timestamp": "2026-08-28T00:15:40..."
  },
  "timestamp": "2026-08-28T00:15:40..."
}
```

**Heartbeat (Server → Client):**
```json
{
  "type": "ping"
}
```

**Client Messages:**
```json
{"type": "ping"}        // Responds with "pong"
{"type": "subscribe"}   // Subscribe to updates
{"type": "unsubscribe"} // Unsubscribe from updates
```

**Status Endpoint:**
```bash
curl http://localhost:8000/ws/status
```

### Development Tools for WebSocket Testing

#### Using Python (Recommended)

```bash
# Install websockets
pip install websockets

# Test script example
python -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        response = await ws.recv()
        print(json.loads(response))

asyncio.run(test())
"
```

#### Using wscat (Node.js required)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/ws"

# With authentication
wscat -c "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"
```

## Rate Limits

| Role | Requests per Minute |
|------|---------------------|
| Guest | 10 |
| User | 100 |
| Admin | 1000 |

## Event-Driven Architecture

### Produced Events
- `AlertAcknowledged` - User acknowledged an alert
- `ExportCompleted` - Export generation completed
- `UserRegistered` - New user registration
- `UserLoggedIn` - User login event

### Consumed Events
- `PredictionGenerated` - New prediction available
- `AlertTriggered` - Alert triggered
- `NotificationSent` - Notification sent
- `PriceUpdated` - Real-time price update (WebSocket)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/test_auth/ -v
pytest tests/unit/test_predictions/ -v
pytest tests/unit/test_market/ -v
pytest tests/unit/test_recommendations/ -v
pytest tests/unit/test_cache/ -v
pytest tests/unit/test_websocket/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | Required |
| `POSTGRES_HOST` | PostgreSQL host | localhost |
| `REDIS_HOST` | Redis host | localhost |
| `RABBITMQ_HOST` | RabbitMQ host | localhost |
| `RATE_LIMIT_GUEST` | Guest rate limit (per minute) | 10 |
| `RATE_LIMIT_USER` | User rate limit (per minute) | 100 |
| `RATE_LIMIT_ADMIN` | Admin rate limit (per minute) | 1000 |

## Docker

```bash
# Build and run with Docker Compose
docker compose up -d

# Run only API Gateway
docker compose up -d api-gateway
```

## Monitoring

- Health check: `GET /health`
- Readiness probe: `GET /ready`
- WebSocket status: `GET /ws/status`
- OpenAPI docs: `GET /docs`

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Write/update tests
4. Submit a pull request

## License

Proprietary - MacroCrypto AI
```