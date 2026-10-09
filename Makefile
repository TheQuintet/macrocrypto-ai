# ============================================
# MACRO-CRYPTO-AI MAKEFILE
# ============================================
# Usage: make <command>
# Example: make help, make up, make logs
# ============================================

.PHONY: help up down restart logs ps build clean test lint format shell

# Default target - show help
.DEFAULT_GOAL := help

# Host port for the MLflow UI (must match docker-compose.override.yml locally)
MLFLOW_HOST_PORT ?= 5000

# Colors for output (if terminal supports)
GREEN  := $(shell tput -Txterm setaf 2 2>/dev/null || echo "")
YELLOW := $(shell tput -Txterm setaf 3 2>/dev/null || echo "")
WHITE  := $(shell tput -Txterm setaf 7 2>/dev/null || echo "")
RESET  := $(shell tput -Txterm sgr0 2>/dev/null || echo "")

# ============================================
# HELP - Show all available commands
# ============================================

help:
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(WHITE)  📊 MACRO-CRYPTO-AI - COMMANDS$(RESET)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)General Commands:$(RESET)"
	@echo "  $(GREEN)make help$(RESET)           - Show this help message"
	@echo "  $(GREEN)make up$(RESET)             - Start all services"
	@echo "  $(GREEN)make down$(RESET)           - Stop all services"
	@echo "  $(GREEN)make restart$(RESET)        - Restart all services"
	@echo "  $(GREEN)make logs$(RESET)           - Show logs for all services"
	@echo "  $(GREEN)make ps$(RESET)             - Show service status"
	@echo "  $(GREEN)make build$(RESET)          - Rebuild and start all services"
	@echo "  $(GREEN)make clean$(RESET)          - Clean Python cache files"
	@echo ""
	@echo "$(YELLOW)Data-Service Commands:$(RESET)"
	@echo "  $(GREEN)make data-up$(RESET)        - Start data-service (rebuilds if needed)"
	@echo "  $(GREEN)make data-down$(RESET)      - Stop data-service"
	@echo "  $(GREEN)make data-logs$(RESET)      - Show data-service logs"
	@echo "  $(GREEN)make data-restart$(RESET)   - Restart data-service"
	@echo "  $(GREEN)make data-shell$(RESET)     - Open shell in data-service"
	@echo "  $(GREEN)make data-test$(RESET)      - Run data-service tests"
	@echo "  $(GREEN)make data-test-unit$(RESET) - Run unit tests only"
	@echo "  $(GREEN)make data-test-int$(RESET)  - Run integration tests only"
	@echo "  $(GREEN)make data-test-e2e$(RESET)  - Run e2e tests only"
	@echo "  $(GREEN)make data-test-cov$(RESET)  - Run tests with coverage"
	@echo "  $(GREEN)make data-lint$(RESET)      - Lint data-service code"
	@echo "  $(GREEN)make data-format$(RESET)    - Format data-service code"
	@echo ""
	@echo "$(YELLOW)AI-Service Commands:$(RESET)"
	@echo "  $(GREEN)make ai-up$(RESET)          - Start ai-service (rebuilds if needed)"
	@echo "  $(GREEN)make ai-down$(RESET)        - Stop ai-service"
	@echo "  $(GREEN)make ai-logs$(RESET)        - Show ai-service logs"
	@echo "  $(GREEN)make ai-restart$(RESET)     - Restart ai-service"
	@echo "  $(GREEN)make ai-shell$(RESET)       - Open shell in ai-service"
	@echo "  $(GREEN)make ai-test$(RESET)        - Run ai-service tests"
	@echo "  $(GREEN)make ai-test-unit$(RESET)   - Run unit tests only"
	@echo "  $(GREEN)make ai-test-int$(RESET)    - Run integration tests only"
	@echo "  $(GREEN)make ai-test-e2e$(RESET)    - Run e2e tests only"
	@echo "  $(GREEN)make ai-test-cov$(RESET)    - Run tests with coverage"
	@echo "  $(GREEN)make ai-health$(RESET)      - Check ai-service health"
	@echo "  $(GREEN)make ai-ready$(RESET)       - Check ai-service readiness"
	@echo "  $(GREEN)make ai-lint$(RESET)        - Lint ai-service code"
	@echo "  $(GREEN)make ai-format$(RESET)      - Format ai-service code"
	@echo "  $(GREEN)make ai-run$(RESET)         - Run ai-service locally"
	@echo "  $(GREEN)make ai-venv$(RESET)        - Create virtual environment"
	@echo "  $(GREEN)make ai-install$(RESET)     - Install dependencies"
	@echo ""
	@echo "$(YELLOW)Alert-Service Commands:$(RESET)"
	@echo "  $(GREEN)make alert-up$(RESET)       - Start alert-service (rebuilds if needed)"
	@echo "  $(GREEN)make alert-down$(RESET)     - Stop alert-service"
	@echo "  $(GREEN)make alert-logs$(RESET)     - Show alert-service logs"
	@echo "  $(GREEN)make alert-restart$(RESET)  - Restart alert-service"
	@echo "  $(GREEN)make alert-shell$(RESET)    - Open shell in alert-service"
	@echo "  $(GREEN)make alert-test$(RESET)     - Run alert-service tests"
	@echo "  $(GREEN)make alert-test-unit$(RESET)- Run unit tests only"
	@echo "  $(GREEN)make alert-test-int$(RESET) - Run integration tests only"
	@echo "  $(GREEN)make alert-test-cov$(RESET) - Run tests with coverage"
	@echo "  $(GREEN)make alert-health$(RESET)   - Check alert-service health"
	@echo "  $(GREEN)make alert-lint$(RESET)     - Lint alert-service code"
	@echo "  $(GREEN)make alert-format$(RESET)   - Format alert-service code"
	@echo ""
	@echo "$(YELLOW)API-Gateway Commands:$(RESET)"
	@echo "  $(GREEN)make api-up$(RESET)          - Start API Gateway (rebuilds if needed)"
	@echo "  $(GREEN)make api-down$(RESET)        - Stop API Gateway"
	@echo "  $(GREEN)make api-logs$(RESET)        - Show API Gateway logs"
	@echo "  $(GREEN)make api-restart$(RESET)     - Restart API Gateway"
	@echo "  $(GREEN)make api-shell$(RESET)       - Open shell in API Gateway"
	@echo "  $(GREEN)make api-health$(RESET)      - Check API Gateway health"
	@echo "  $(GREEN)make api-ready$(RESET)       - Check API Gateway readiness"
	@echo "  $(GREEN)make api-test$(RESET)        - Run API Gateway tests"
	@echo "  $(GREEN)make api-test-unit$(RESET)   - Run unit tests only"
	@echo "  $(GREEN)make api-test-int$(RESET)    - Run integration tests only"
	@echo "  $(GREEN)make api-test-e2e$(RESET)    - Run e2e tests only"
	@echo "  $(GREEN)make api-test-cov$(RESET)    - Run tests with coverage"
	@echo "  $(GREEN)make api-lint$(RESET)        - Lint API Gateway code"
	@echo "  $(GREEN)make api-format$(RESET)      - Format API Gateway code"
	@echo "  $(GREEN)make api-run$(RESET)         - Run API Gateway locally"
	@echo "  $(GREEN)make api-venv$(RESET)        - Create virtual environment"
	@echo "  $(GREEN)make api-install$(RESET)     - Install dependencies"
	@echo ""
	@echo "$(YELLOW)Infrastructure Commands:$(RESET)"
	@echo "  $(GREEN)make redis-cli$(RESET)      - Open Redis CLI"
	@echo "  $(GREEN)make postgres-cli$(RESET)   - Open PostgreSQL CLI"
	@echo "  $(GREEN)make rabbitmq-ui$(RESET)    - Open RabbitMQ Management UI"
	@echo "  $(GREEN)make mlflow-ui$(RESET)      - Open MLflow UI"
	@echo ""
	@echo "$(YELLOW)Development Commands:$(RESET)"
	@echo "  $(GREEN)make setup$(RESET)          - Setup development environment"
	@echo "  $(GREEN)make venv$(RESET)           - Create virtual environment"
	@echo "  $(GREEN)make install$(RESET)        - Install dependencies"
	@echo "  $(GREEN)make run$(RESET)            - Run data-service locally"
	@echo ""
	@echo "$(YELLOW)Monitoring Commands:$(RESET)"
	@echo "  $(GREEN)make health$(RESET)         - Check service health"
	@echo "  $(GREEN)make price$(RESET)          - Get current BTC price"
	@echo "  $(GREEN)make watch-price$(RESET)    - Live BTC price tracking"
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"

# ============================================
# GENERAL DOCKER COMPOSE COMMANDS
# ============================================

up:
	docker compose up -d

down:
	docker compose down

down-clean:
	docker compose down -v

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

build:
	docker compose up -d --build

# ============================================
# DATA-SERVICE COMMANDS
# ============================================

data-up:
	docker compose up -d --build data-service
	@echo "✅ Data-service started. View logs with: make data-logs"

data-down:
	docker compose stop data-service
	docker compose rm -f data-service
	@echo "✅ Data-service stopped"

data-logs:
	docker compose logs -f data-service

data-restart:
	docker compose restart data-service
	@echo "✅ Data-service restarted"

data-shell:
	docker compose exec data-service /bin/bash

# ============================================
# DATA-SERVICE TEST COMMANDS
# ============================================

data-test:
	@echo "🧪 Running all tests..."
	docker compose exec data-service pytest tests/ -v

data-test-unit:
	@echo "🧪 Running unit tests..."
	docker compose exec data-service pytest tests/unit/ -v

data-test-int:
	@echo "🧪 Running integration tests..."
	docker compose exec data-service pytest tests/integration/ -v

data-test-e2e:
	@echo "🧪 Running e2e tests..."
	docker compose exec data-service pytest tests/e2e/ -v

data-test-cov:
	@echo "🧪 Running tests with coverage..."
	docker compose exec data-service pytest tests/ --cov=app --cov-report=term --cov-report=html
	@echo "📊 Coverage report: services/data-service/htmlcov/index.html"

data-test-file:
	@echo "🧪 Running test file: $(FILE)"
	docker compose exec data-service pytest $(FILE) -v

data-test-verbose:
	@echo "🧪 Running tests with verbose output..."
	docker compose exec data-service pytest tests/ -v -s --tb=long

data-test-quick:
	@echo "🧪 Running tests (skip slow)..."
	docker compose exec data-service pytest tests/ -v -k "not slow"

# ============================================
# AI-SERVICE COMMANDS
# ============================================

ai-up:
	docker compose up -d --build ai-service
	@echo "✅ AI-service started. View logs with: make ai-logs"

ai-down:
	docker compose stop ai-service
	docker compose rm -f ai-service
	@echo "✅ AI-service stopped"

ai-logs:
	docker compose logs -f ai-service

ai-restart:
	docker compose restart ai-service
	@echo "✅ AI-service restarted"

ai-shell:
	docker compose exec ai-service /bin/bash

# ============================================
# AI-SERVICE TEST COMMANDS
# ============================================

ai-test:
	@echo "🧪 Running all tests..."
	docker compose exec ai-service pytest tests/ -v

ai-test-unit:
	@echo "🧪 Running unit tests..."
	docker compose exec ai-service pytest tests/unit/ -v

ai-test-int:
	@echo "🧪 Running integration tests..."
	docker compose exec ai-service pytest tests/integration/ -v

ai-test-e2e:
	@echo "🧪 Running e2e tests..."
	docker compose exec ai-service pytest tests/e2e/ -v

ai-test-cov:
	@echo "🧪 Running tests with coverage..."
	docker compose exec ai-service pytest tests/ --cov=app --cov-report=term --cov-report=html
	@echo "📊 Coverage report: services/ai-service/htmlcov/index.html"

ai-test-file:
	@echo "🧪 Running test file: $(FILE)"
	docker compose exec ai-service pytest $(FILE) -v

ai-test-verbose:
	@echo "🧪 Running tests with verbose output..."
	docker compose exec ai-service pytest tests/ -v -s --tb=long

ai-test-quick:
	@echo "🧪 Running tests (skip slow)..."
	docker compose exec ai-service pytest tests/ -v -k "not slow"

# ============================================
# AI-SERVICE HEALTH CHECK
# ============================================

ai-health:
	@echo "🏥 Checking ai-service health..."
	@curl -s http://localhost:8002/health | jq || echo "❌ AI service not running or jq not installed"

ai-ready:
	@echo "🔄 Checking ai-service readiness..."
	@curl -s http://localhost:8002/ready | jq || echo "❌ AI service not ready or jq not installed"

# ============================================
# AI-SERVICE LINTING & FORMATTING
# ============================================

ai-lint:
	docker compose exec ai-service ruff check app/ || echo "⚠️  Lint issues found"

ai-format:
	docker compose exec ai-service black app/ --line-length=120

# ============================================
# AI-SERVICE DEVELOPMENT COMMANDS
# ============================================

ai-run:
	@echo "🚀 Running AI Service locally..."
	cd services/ai-service && . venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

ai-venv:
	@echo "🔧 Creating virtual environment for AI Service..."
	cd services/ai-service && python3 -m venv venv
	@echo "✅ Virtual environment created"

ai-install:
	@echo "📦 Installing AI Service dependencies..."
	cd services/ai-service && source venv/bin/activate && pip install -r requirements-dev.txt
	@echo "✅ Dependencies installed"

# ============================================
# AI-SERVICE TEST COMMANDS (LOCAL)
# ============================================

ai-test-local:
	@echo "🧪 Running all tests locally..."
	cd services/ai-service && . venv/bin/activate && TESTING=true pytest tests/ -v

ai-test-local-unit:
	@echo "🧪 Running unit tests locally..."
	cd services/ai-service && . venv/bin/activate && TESTING=true pytest tests/ -m unit -v

ai-test-local-cov:
	@echo "🧪 Running tests with coverage locally..."
	cd services/ai-service && . venv/bin/activate && TESTING=true pytest tests/ --cov=app --cov-report=term --cov-report=html
	@echo "📊 Coverage report: services/ai-service/htmlcov/index.html"

ai-test-local-file:
	@echo "🧪 Running test file locally: $(FILE)"
	cd services/ai-service && . venv/bin/activate && TESTING=true pytest $(FILE) -v

# ============================================
# ALERT-SERVICE COMMANDS
# ============================================

alert-up:
	docker compose up -d --build alert-service
	@echo "✅ Alert-service started. View logs with: make alert-logs"

alert-down:
	docker compose stop alert-service
	docker compose rm -f alert-service
	@echo "✅ Alert-service stopped"

alert-logs:
	docker compose logs -f alert-service

alert-restart:
	docker compose restart alert-service
	@echo "✅ Alert-service restarted"

alert-shell:
	docker compose exec alert-service /bin/bash

# ============================================
# ALERT-SERVICE TEST COMMANDS
# ============================================

alert-test:
	@echo "🧪 Running all tests..."
	docker compose exec alert-service pytest tests/ -v

alert-test-unit:
	@echo "🧪 Running unit tests..."
	docker compose exec alert-service pytest tests/unit/ -v

alert-test-int:
	@echo "🧪 Running integration tests..."
	docker compose exec alert-service pytest tests/integration/ -v

alert-test-cov:
	@echo "🧪 Running tests with coverage..."
	docker compose exec alert-service pytest tests/ --cov=app --cov-report=term --cov-report=html
	@echo "📊 Coverage report: services/alert-service/htmlcov/index.html"

alert-test-file:
	@echo "🧪 Running test file: $(FILE)"
	docker compose exec alert-service pytest $(FILE) -v

alert-test-verbose:
	@echo "🧪 Running tests with verbose output..."
	docker compose exec alert-service pytest tests/ -v -s --tb=long

alert-test-quick:
	@echo "🧪 Running tests (skip slow)..."
	docker compose exec alert-service pytest tests/ -v -k "not slow"

# ============================================
# ALERT-SERVICE HEALTH CHECK
# ============================================

alert-health:
	@echo "🏥 Checking alert-service health..."
	@curl -s http://localhost:8003/health | jq || echo "❌ Alert service not running or jq not installed"

alert-ready:
	@echo "🔄 Checking alert-service readiness..."
	@curl -s http://localhost:8003/ready | jq || echo "❌ Alert service not ready or jq not installed"

# ============================================
# ALERT-SERVICE LINTING & FORMATTING
# ============================================

alert-lint:
	docker compose exec alert-service ruff check app/ || echo "⚠️  Lint issues found"

alert-format:
	docker compose exec alert-service black app/ --line-length=120

# ============================================
# API-GATEWAY COMMANDS
# ============================================

api-up:
	docker compose up -d --build api-gateway
	@echo "✅ API Gateway started. View logs with: make api-logs"

api-down:
	docker compose stop api-gateway
	docker compose rm -f api-gateway
	@echo "✅ API Gateway stopped"

api-logs:
	docker compose logs -f api-gateway

api-restart:
	docker compose restart api-gateway
	@echo "✅ API Gateway restarted"

api-shell:
	docker compose exec api-gateway /bin/sh

api-health:
	@echo "🏥 Checking API Gateway health..."
	@curl -s http://localhost:8000/health | jq || echo "❌ API Gateway not running or jq not installed"

api-ready:
	@echo "🔄 Checking API Gateway readiness..."
	@curl -s http://localhost:8000/ready | jq || echo "❌ API Gateway not ready or jq not installed"

# ============================================
# API-GATEWAY TEST COMMANDS
# ============================================

api-test:
	@echo "🧪 Running all tests..."
	docker compose exec api-gateway pytest tests/ -v

api-test-unit:
	@echo "🧪 Running unit tests..."
	docker compose exec api-gateway pytest tests/unit/ -v

api-test-int:
	@echo "🧪 Running integration tests..."
	docker compose exec api-gateway pytest tests/integration/ -v

api-test-e2e:
	@echo "🧪 Running e2e tests..."
	docker compose exec api-gateway pytest tests/e2e/ -v

api-test-cov:
	@echo "🧪 Running tests with coverage..."
	docker compose exec api-gateway pytest tests/ --cov=app --cov-report=term --cov-report=html
	@echo "📊 Coverage report: services/api-gateway/htmlcov/index.html"

api-test-file:
	@echo "🧪 Running test file: $(FILE)"
	docker compose exec api-gateway pytest $(FILE) -v

api-test-verbose:
	@echo "🧪 Running tests with verbose output..."
	docker compose exec api-gateway pytest tests/ -v -s --tb=long

api-test-quick:
	@echo "🧪 Running tests (skip slow)..."
	docker compose exec api-gateway pytest tests/ -v -k "not slow"

# ============================================
# API-GATEWAY LINTING & FORMATTING
# ============================================

api-lint:
	docker compose exec api-gateway ruff check app/ || echo "⚠️  Lint issues found"

api-format:
	docker compose exec api-gateway black app/ --line-length=120

# ============================================
# API-GATEWAY DEVELOPMENT COMMANDS
# ============================================

api-run:
	@echo "🚀 Running API Gateway locally..."
	cd services/api-gateway && . venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-venv:
	@echo "🔧 Creating virtual environment for API Gateway..."
	cd services/api-gateway && python3 -m venv venv
	@echo "✅ Virtual environment created"

api-install:
	@echo "📦 Installing API Gateway dependencies..."
	cd services/api-gateway && source venv/bin/activate && pip install -r requirements-dev.txt
	@echo "✅ Dependencies installed"

# ============================================
# API-GATEWAY TEST COMMANDS (LOCAL)
# ============================================

api-test-local:
	@echo "🧪 Running all tests locally..."
	cd services/api-gateway && . venv/bin/activate && TESTING=true pytest tests/ -v

api-test-local-unit:
	@echo "🧪 Running unit tests locally..."
	cd services/api-gateway && . venv/bin/activate && TESTING=true pytest tests/ -m unit -v

api-test-local-cov:
	@echo "🧪 Running tests with coverage locally..."
	cd services/api-gateway && . venv/bin/activate && TESTING=true pytest tests/ --cov=app --cov-report=term --cov-report=html
	@echo "📊 Coverage report: services/api-gateway/htmlcov/index.html"

api-test-local-file:
	@echo "🧪 Running test file locally: $(FILE)"
	cd services/api-gateway && . venv/bin/activate && TESTING=true pytest $(FILE) -v

# ============================================
# LINTING & FORMATTING (Data Service)
# ============================================

data-lint:
	docker compose exec data-service flake8 app/ --max-line-length=120 || echo "⚠️  Lint issues found"

data-format:
	docker compose exec data-service black app/ --line-length=120

# ============================================
# INFRASTRUCTURE COMMANDS
# ============================================

redis-cli:
	docker compose exec redis redis-cli

postgres-cli:
	docker compose exec postgres psql -U macro -d macrocrypto

rabbitmq-ui:
	@echo "🌐 Opening RabbitMQ Management UI..."
	@echo "   URL: http://localhost:15672"
	@echo "   Username: guest"
	@echo "   Password: guest"
	@xdg-open http://localhost:15672 2>/dev/null || open http://localhost:15672 2>/dev/null || echo "Open http://localhost:15672 in your browser"

mlflow-ui:
	@echo "🌐 Opening MLflow UI..."
	@echo "   URL: http://localhost:$(MLFLOW_HOST_PORT)"
	@xdg-open http://localhost:$(MLFLOW_HOST_PORT) 2>/dev/null || open http://localhost:$(MLFLOW_HOST_PORT) 2>/dev/null || echo "Open http://localhost:$(MLFLOW_HOST_PORT) in your browser"

# ============================================
# DEVELOPMENT SETUP COMMANDS
# ============================================

setup: venv install
	@echo "✅ Development environment ready!"
	@echo "   Activate with: source services/data-service/venv/bin/activate"

venv:
	@echo "🔧 Creating virtual environment..."
	cd services/data-service && python3 -m venv venv
	@echo "✅ Virtual environment created"

install:
	@echo "📦 Installing dependencies..."
	cd services/data-service && source venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed"

run:
	@echo "🚀 Running data-service locally..."
	cd services/data-service && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# ============================================
# CLEANUP COMMANDS
# ============================================

clean:
	@echo "🧹 Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned cache files"

clean-all: clean
	@echo "🧹 Cleaning Docker volumes..."
	docker compose down -v
	@echo "✅ Cleaned everything"

# ============================================
# LOGGING COMMANDS
# ============================================

tail-logs:
	docker compose logs --tail=50 data-service

watch-logs:
	docker compose logs -f data-service | grep -i "btc price\|error\|exception"

watch-websocket:
	docker compose logs -f data-service | grep -i "websocket\|btc price\|connected"

# ============================================
# STATUS COMMANDS
# ============================================

health:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8001/health | jq || echo "❌ Service not running or jq not installed"

price:
	@echo "💰 Getting BTC price..."
	@curl -s http://localhost:8001/api/v1/btc/price | jq || echo "❌ Service not running or jq not installed"

watch-price:
	@echo "📊 Watching BTC price... (Ctrl+C to stop)"
	@while true; do \
		clear; \
		echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
		echo "  📊 BTC LIVE PRICE"; \
		echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
		curl -s http://localhost:8001/api/v1/btc/price | jq -r '"  💰 Price: $\(.current_price)\n  📈 24h: \(.change_24h_percent)%\n  📉 7d: \(.change_7d_percent)%\n  🕐 Updated: \(.updated_at)"' 2>/dev/null || echo "  ❌ Service not running"; \
		echo ""; \
		echo "  🔄 Press Ctrl+C to exit"; \
		sleep 2; \
	done

# ============================================
# DEPLOYMENT COMMANDS
# ============================================

deploy:
	@echo "🚀 Deploying..."
	docker compose down
	docker compose up -d --build
	@echo "✅ Deployment complete"
	@echo "📊 Check logs: make logs"