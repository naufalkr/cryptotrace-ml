.PHONY: help build up down start stop restart logs clean dev prod pipeline shell db-shell test

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)CryptoTrace ML - Docker Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

setup: ## Initial setup (copy env file)
	@echo "$(BLUE)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo "$(GREEN)✓ Created .env file from .env.docker$(NC)"; \
		echo "$(YELLOW)⚠ Please edit .env and set your database password$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

up: ## Start all services in detached mode
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)Monitor logs with: make logs$(NC)"

down: ## Stop and remove containers
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

start: ## Start existing containers
	@echo "$(BLUE)Starting containers...$(NC)"
	docker-compose start
	@echo "$(GREEN)✓ Containers started$(NC)"

stop: ## Stop containers without removing
	@echo "$(BLUE)Stopping containers...$(NC)"
	docker-compose stop
	@echo "$(GREEN)✓ Containers stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

logs: ## Show logs (use 'make logs s=cryptotrace-ml' for specific service)
	@echo "$(BLUE)Showing logs... (Ctrl+C to exit)$(NC)"
	docker-compose logs -f $(s)

status: ## Show status of all containers
	@echo "$(BLUE)Container Status:$(NC)"
	@docker-compose ps

pipeline: ## Run pipeline manually
	@echo "$(BLUE)Running pipeline manually...$(NC)"
	docker-compose exec cryptotrace-ml /run-pipeline.sh
	@echo "$(GREEN)✓ Pipeline execution complete$(NC)"

shell: ## Open shell in ML container
	@echo "$(BLUE)Opening shell in cryptotrace-ml container...$(NC)"
	docker-compose exec cryptotrace-ml /bin/bash

db-shell: ## Open PostgreSQL shell
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	docker-compose exec postgres psql -U postgres -d cryptotrace

collect: ## Collect data from database manually
	@echo "$(BLUE)Collecting data...$(NC)"
	docker-compose exec cryptotrace-ml python collect_data.py --limit-tx $${LIMIT_TX:-1000}

train: ## Train new models
	@echo "$(BLUE)Training new models...$(NC)"
	docker-compose exec cryptotrace-ml python main.py --mode train

predict: ## Run prediction with existing models
	@echo "$(BLUE)Running predictions...$(NC)"
	docker-compose exec cryptotrace-ml python main.py --mode predict

update-db: ## Update database with risk scores
	@echo "$(BLUE)Updating database...$(NC)"
	docker-compose exec cryptotrace-ml bash -c 'echo "yes" | python update_risk_scores.py --batch-size $${BATCH_SIZE:-200}'

graph: ## Run graph investigation
	@echo "$(BLUE)Running graph analysis...$(NC)"
	docker-compose exec cryptotrace-ml python graph_investigation.py

clean: ## Remove containers, volumes, and generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker-compose down -v
	@echo "$(YELLOW)⚠ Removing generated files (data, models, reports)...$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/* models/* reports/*; \
		echo "$(GREEN)✓ Cleanup complete$(NC)"; \
	else \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

dev: ## Start with development volumes mounted
	@echo "$(BLUE)Starting in development mode...$(NC)"
	@echo "$(YELLOW)⚠ Source code will be mounted from host$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✓ Development environment started$(NC)"

prod: ## Start in production mode
	@echo "$(BLUE)Starting in production mode...$(NC)"
	docker-compose up -d --build
	@echo "$(GREEN)✓ Production environment started$(NC)"

admin: ## Start with PgAdmin
	@echo "$(BLUE)Starting with PgAdmin...$(NC)"
	docker-compose --profile admin up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)PgAdmin available at: http://localhost:5050$(NC)"

backup-db: ## Backup PostgreSQL database
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@docker-compose exec -T postgres pg_dump -U postgres cryptotrace > backups/cryptotrace_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backed up to backups/$(NC)"

restore-db: ## Restore PostgreSQL database (use 'make restore-db file=backup.sql')
	@echo "$(BLUE)Restoring database from $(file)...$(NC)"
	@if [ -z "$(file)" ]; then \
		echo "$(YELLOW)Usage: make restore-db file=backups/backup.sql$(NC)"; \
		exit 1; \
	fi
	@cat $(file) | docker-compose exec -T postgres psql -U postgres cryptotrace
	@echo "$(GREEN)✓ Database restored$(NC)"

stats: ## Show container resource usage
	@echo "$(BLUE)Container Resource Usage:$(NC)"
	@docker stats --no-stream

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	docker-compose exec cryptotrace-ml python -m pytest tests/
	@echo "$(GREEN)✓ Tests complete$(NC)"

rebuild: down build up ## Rebuild and restart all services

# Default target
.DEFAULT_GOAL := help
