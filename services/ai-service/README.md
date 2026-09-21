# AI Service — MacroCrypto AI

## Overview

The AI Service is the intelligence engine of MacroCrypto AI. It generates Bitcoin price predictions using multiple machine learning models (Prophet, XGBoost, LightGBM) driven by macroeconomic data.

## Architecture Context

This service is part of an event-driven microservices architecture:

| Service | Responsibility |
|---------|----------------|
| **Data Ingestion Service** | Collects crypto and economic data |
| **AI Service** (this) | Generates BTC price predictions |
| **API Gateway** | Serves REST APIs |
| **Alert Service** | Sends notifications |

## Responsibilities

- Consume `PriceUpdated` and `IndicatorUpdated` events from RabbitMQ
- Engineer 10 features (5 macro + 5 BTC)
- Train and retrain 6 model versions (Prophet, XGBoost, LightGBM × 2 strategies each)
- Generate 24-hour and 7-day predictions with confidence intervals
- Publish `PredictionGenerated` events
- Track performance metrics (MAE, RMSE, MAPE)
- Cache predictions in Redis
- Version models with MLflow

## Events

### Consumed

| Event | Source |
|-------|--------|
| `PriceUpdated` | Data Ingestion Service |
| `IndicatorUpdated` | Data Ingestion Service |

### Produced

| Event | Consumer |
|-------|----------|
| `PredictionGenerated` | Alert Service, API Gateway |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| Web Framework | FastAPI |
| ML Models | Prophet, XGBoost, LightGBM |
| Model Registry | MLflow |
| Database | TimescaleDB |
| Cache | Redis |
| Message Broker | RabbitMQ |
| Scheduling | APScheduler |

## Local Setup

### Prerequisites

- Python 3.13
- Docker & Docker Compose
- Make (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install-dev
# or
pip install -r requirements-dev.txt