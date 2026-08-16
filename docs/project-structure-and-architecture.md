# MacroCrypto AI - Project Structure & Architecture

## Overview
**MacroCrypto AI** is an event-driven microservices platform that combines real-time Bitcoin market data with macroeconomic indicators (inflation, interest rates, GDP) to deliver AI-powered intelligence and price forecasting through a web dashboard and REST API.

---

## Project Structure


```
macro-crypto-ai/
├── docker-compose.yml
├── .env.example
├── README.md
├── Makefile                                 # Common commands (up, down, logs, test)
│
├── services/
│   ├── data-service/                        # Data collection & event publisher
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                      # FastAPI entry point
│   │   │   ├── config.py                    # Environment configuration
│   │   │   │
│   │   │   ├── collectors/                  # Data source collectors
│   │   │   │   ├── __init__.py
│   │   │   │   ├── coingecko.py             # OHLCV, price, volume, market cap
│   │   │   │   ├── binance.py               # Real-time WebSocket BTC/USDT
│   │   │   │   └── fred.py                  # Economic indicators (CPI, Interest Rate, GDP)
│   │   │   │
│   │   │   ├── websocket/                   # Real-time data processing
│   │   │   │   ├── __init__.py
│   │   │   │   └── btc_client.py            # Binance WebSocket handler
│   │   │   │
│   │   │   ├── rabbitmq/                    # Event publishing
│   │   │   │   ├── __init__.py
│   │   │   │   └── producer.py              # Publish price_update & economic_update
│   │   │   │
│   │   │   ├── api/                         # Internal API endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py                # Health checks, service status
│   │   │   │
│   │   │   ├── database/                    # Data storage
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py                # SQLAlchemy models (CryptoPrices, EconomicIndicators)
│   │   │   │   └── session.py               # Database connection & session management
│   │   │   │
│   │   │   ├── cache/                       # Redis caching
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py                # Redis connection & caching logic
│   │   │   │
│   │   │   └── utils/                       # Shared utilities
│   │   │       ├── __init__.py
│   │   │       ├── validators.py            # Data validation
│   │   │       └── transformers.py          # Data transformation
│   │   └── venv/
│   │
│   ├── ai-service/                          # AI forecasting (Consumer + Publisher)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                      # FastAPI entry point
│   │   │   ├── config.py
│   │   │   │
│   │   │   ├── rabbitmq/                    # Event consumption & publishing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── consumer.py              # Consume price_update & economic_update
│   │   │   │   └── publisher.py             # Publish forecast_event
│   │   │   │
│   │   │   ├── ai/                          # AI/ML models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── prophet_model.py         # Facebook Prophet forecasting
│   │   │   │   ├── feature_engineering.py   # Feature preparation
│   │   │   │   └── trainer.py               # Model training & retraining logic
│   │   │   │
│   │   │   ├── database/                    # Access to historical data
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py                # Forecast models (forecasts table)
│   │   │   │   └── session.py               # DB connection
│   │   │   │
│   │   │   ├── cache/                       # Redis caching for predictions
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py                # Cache forecast results
│   │   │   │
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── metrics.py               # Model evaluation metrics (MAE, RMSE)
│   │   └── venv/
│   │
│   ├── alert-service/                       # Alert evaluation (Consumer)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   │
│   │   │   ├── rabbitmq/                    # Event consumption
│   │   │   │   ├── __init__.py
│   │   │   │   └── consumer.py              # Consume all event types
│   │   │   │
│   │   │   ├── alert/                       # Alert engine
│   │   │   │   ├── __init__.py
│   │   │   │   ├── rules.py                 # Rule evaluation engine
│   │   │   │   ├── conditions.py            # Condition builders (price > x, inflation < y, etc.)
│   │   │   │   └── notifier.py              # Email notifications (SMTP)
│   │   │   │
│   │   │   ├── database/                    # Alert storage
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py                # AlertRules, AlertHistory
│   │   │   │   └── session.py               # DB connection
│   │   │   │
│   │   │   └── utils/
│   │   │       └── __init__.py
│   │   └── venv/
│   │
│   └── api-gateway/                         # External API & Dashboard backend
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── .env.example
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py                      # FastAPI entry point
│       │   ├── config.py
│       │   │
│       │   ├── routes/                      # REST API endpoints
│       │   │   ├── __init__.py
│       │   │   ├── btc.py                   # GET /api/btc/price, /api/btc/history
│       │   │   ├── economic.py              # GET /api/economic/inflation, /rates, /gdp
│       │   │   ├── forecast.py              # GET /api/forecast
│       │   │   └── alerts.py                # POST/GET/DELETE /api/alerts
│       │   │
│       │   ├── auth/                        # Authentication
│       │   │   ├── __init__.py
│       │   │   ├── jwt.py                   # JWT token handling
│       │   │   └── dependencies.py          # FastAPI dependency injection
│       │   │
│       │   ├── database/                    # User & alert data
│       │   │   ├── __init__.py
│       │   │   ├── models.py                # Users, AlertRules, AlertHistory
│       │   │   └── session.py               # DB connection
│       │   │
│       │   ├── cache/                       # Redis cache access
│       │   │   ├── __init__.py
│       │   │   └── client.py                # Read cached data for fast responses
│       │   │
│       │   └── websocket/                   # Future: Real-time updates
│       │       ├── __init__.py
│       │       └── manager.py               # WebSocket connection manager
│       └── venv/
│
├── shared/                                  # Shared code across all services
│   ├── __init__.py
│   ├── models/                              # Pydantic shared models
│   │   ├── __init__.py
│   │   ├── price.py                         # CryptoPrice, PriceUpdate
│   │   ├── economic.py                      # EconomicIndicator, EconomicUpdate
│   │   ├── forecast.py                      # Forecast, ForecastEvent
│   │   └── alert.py                         # AlertRule, AlertHistory
│   │
│   ├── rabbitmq/                            # Shared RabbitMQ utilities
│   │   ├── __init__.py
│   │   ├── client.py                        # Connection pool & channel management
│   │   ├── exchanges.py                     # Exchange definitions
│   │   └── events.py                        # Event type definitions & schemas
│   │
│   └── database/                            # Shared database utilities
│       ├── __init__.py
│       └── base.py                          # SQLAlchemy Base class
│
├── frontend/                                # React Dashboard
│   ├── package.json
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.js
│   │   ├── api/                             # API client
│   │   │   ├── client.js                    # Axios configuration
│   │   │   └── endpoints.js                 # API endpoint functions
│   │   │
│   │   ├── components/                      # React components
│   │   │   ├── dashboard/
│   │   │   │   ├── PriceChart.jsx
│   │   │   │   ├── EconomicIndicators.jsx
│   │   │   │   └── ForecastDisplay.jsx
│   │   │   │
│   │   │   ├── alerts/
│   │   │   │   ├── AlertList.jsx
│   │   │   │   ├── AlertForm.jsx
│   │   │   │   └── AlertHistory.jsx
│   │   │   │
│   │   │   └── common/
│   │   │       ├── Navbar.jsx
│   │   │       ├── Footer.jsx
│   │   │       └── LoadingSpinner.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Alerts.jsx
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   │
│   │   ├── hooks/                           # Custom React hooks
│   │   │   ├── useAuth.js
│   │   │   └── useWebSocket.js
│   │   │
│   │   └── utils/
│   │       ├── format.js                    # Number/date formatting
│   │       └── validation.js                # Form validation
│   └── venv/
│
├── infrastructure/                          # Infrastructure as Code
│   ├── nginx/
│   │   └── nginx.conf                       # Reverse proxy configuration
│   ├── scripts/
│   │   ├── init-db.sql                      # Database initialization
│   │   └── seed-data.sql                    # Seed data for development
│   └── monitoring/
│       ├── prometheus.yml                   # Metrics collection
│       └── grafana/                         # Dashboards (future)
│
└── scripts/                                 # Utility scripts
    ├── setup.sh                             # Development environment setup
    ├── seed_db.py                           # Seed database with sample data
    ├── run_tests.sh                         # Run all tests
    └── deploy.sh                            # Deployment script
```