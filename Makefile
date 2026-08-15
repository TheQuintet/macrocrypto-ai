# ============================================
# MACRO-CRYPTO-AI MAKEFILE
# ============================================
# Usage: make <command>
# Example: make help, make up, make logs
# ============================================

.PHONY: help up down restart logs ps build clean test lint format shell

# Default target - show help
.DEFAULT_GOAL := help

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
	@echo "$(YELLOW)Infrastructure Commands:$(RESET)"
	@echo "  $(GREEN)make redis-cli$(RESET)      - Open Redis CLI"
	@echo "  $(GREEN)make postgres-cli$(RESET)   - Open PostgreSQL CLI"
	@echo "  $(GREEN)make rabbitmq-ui$(RESET)    - Open RabbitMQ Management UI"
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