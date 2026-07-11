.PHONY: help dev test lint format type-check docker-build docker-up docker-down migrate clean install

# Default Python
PYTHON ?= python

# Colors for terminal output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RESET  := \033[0m

help: ## Show this help message
	@echo "Meridian — Development Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}'

# ============================================================
# Development
# ============================================================

install: ## Install project with all dependencies
	pip install -e ".[dev,test,ai]"
	pre-commit install

dev: ## Start local development server
	uvicorn services.api_gateway.finance_assistant.main:app --reload --host 0.0.0.0 --port 8000

# ============================================================
# Quality
# ============================================================

lint: ## Run linter (ruff)
	ruff check .
	ruff format --check .

format: ## Auto-format code
	ruff check --fix .
	ruff format .

type-check: ## Run type checker (mypy)
	mypy services/

check: lint type-check ## Run all static checks

# ============================================================
# Testing
# ============================================================

test: ## Run all tests with coverage
	pytest

test-unit: ## Run unit tests only
	pytest -m "not integration and not slow"

test-integration: ## Run integration tests
	pytest -m integration

test-fast: ## Run tests without coverage (faster)
	pytest --no-cov -q

# ============================================================
# Docker
# ============================================================

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start all services (detached)
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail logs from all services
	docker compose logs -f

docker-clean: ## Remove containers, volumes, and images
	docker compose down -v --rmi local

# ============================================================
# Database
# ============================================================

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	alembic revision --autogenerate -m "$(MSG)"

migrate-downgrade: ## Rollback last migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history --verbose

# ============================================================
# Infrastructure
# ============================================================

tf-init: ## Initialize Terraform
	cd infrastructure/terraform/envs/dev && terraform init

tf-plan: ## Plan Terraform changes
	cd infrastructure/terraform/envs/dev && terraform plan

tf-apply: ## Apply Terraform changes
	cd infrastructure/terraform/envs/dev && terraform apply

tf-destroy: ## Destroy Terraform resources
	cd infrastructure/terraform/envs/dev && terraform destroy

# ============================================================
# Cleanup
# ============================================================

clean: ## Remove all build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage
