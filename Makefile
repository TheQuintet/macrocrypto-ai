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
	@echo "  $(GREEN)make data-up$(RESET)        - Start data-service"
	@echo "  $(GREEN)make data-down$(RESET)      - Stop data-service"
	@echo "  $(GREEN)make data-logs$(RESET)      - Show data-service logs"
	@echo "  $(GREEN)make data-restart$(RESET)   - Restart data-service"
	@echo "  $(GREEN)make data-shell$(RESET)     - Open shell in data-service"
	@echo "  $(GREEN)make data-test$(RESET)      - Run data-service tests"
	@echo "  $(GREEN)make data-lint$(RESET)      - Lint data-service code"
	@echo "  $(GREEN)make data-format$(RESET)    - Format data-service code"
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

data-test:
	docker compose exec data-service pytest -v

data-test-unit:
	docker compose exec data-service pytest -m unit -v

data-test-integration:
	docker compose exec data-service pytest -m integration -v

data-test-coverage:
	docker compose exec data-service pytest --cov=app --cov-report=html
	@echo "📊 Coverage report: services/data-service/htmlcov/index.html"

data-lint:
	docker compose exec data-service flake8 app/ --max-line-length=120

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