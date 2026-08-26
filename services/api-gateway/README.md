# API Gateway Service

MacroCrypto AI API Gateway - REST API gateway for internal microservices.

## Overview

The API Gateway is the entry point for all client requests. It routes requests to internal microservices, handles authentication, rate limiting, and request/response transformation.

## Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | REST API entry point |
| Cache | Redis | Session management, rate limiting |
| Message Broker | RabbitMQ | Event consumption/production |
| Service Calls | HTTPX | Internal service communication |

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