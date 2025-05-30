.PHONY: help build run test clean lint format install dev-setup docker-build docker-run

# Default target
help: ## Show this help message
	@echo "Recipe Cost & Nutrition API - Development Commands"
	@echo "=================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Setup
install: ## Install Python dependencies
	pip install --upgrade pip
	pip install -r requirements.txt

# Code Quality
lint: ## Run linting checks
	flake8 main.py test_main.py database.py load_data.py init_postgres.py --extend-ignore=E203,W503
	mypy main.py database.py load_data.py init_postgres.py --ignore-missing-imports

format: ## Format code with black and isort
	black main.py test_main.py database.py load_data.py init_postgres.py
	# isort main.py test_main.py database.py load_data.py init_postgres.py

format-check: ## Check code formatting
	black --check --diff main.py test_main.py database.py load_data.py init_postgres.py
	# isort --check-only --diff main.py test_main.py database.py load_data.py init_postgres.py

# Testing
test: ## Run unit tests
	TESTING=true pytest test_main.py -v

test-coverage: ## Run tests with coverage report
	TESTING=true pytest test_main.py --cov=main --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	TESTING=true pytest-watch -- test_main.py -v

# Docker Compose Testing
test-docker: ## Run tests in Docker environment
	docker compose up -d postgres redis
	sleep 10
	docker compose run --rm -e TESTING=true recipe-api python -m pytest test_main.py -v
	docker compose down

test-docker-clean: ## Run tests in clean Docker environment
	docker compose down -v
	docker compose up -d postgres redis
	sleep 10
	docker compose run --rm -e TESTING=true recipe-api python -m pytest test_main.py -v
	docker compose down

test-docker-logs: ## Show Docker compose logs
	docker compose logs -f

# Local Development
run: ## Run the application locally
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the application in production mode
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker Commands
docker-build: ## Build Docker image
	docker build -t recipe-api:latest .

docker-run: ## Run application in Docker container
	docker run -d --name recipe-api -p 8000:8000 \
		-v $(PWD)/sample-data:/app/sample-data:ro \
		recipe-api:latest

docker-stop: ## Stop and remove Docker container
	docker stop recipe-api || true
	docker rm recipe-api || true

# Docker Compose Commands
up: ## Start services with docker compose
	docker compose up --build

up-prod: ## Start services in production mode
	docker compose --profile production up -d

down: ## Stop docker compose services
	docker compose down

logs: ## Show docker compose logs
	docker compose logs -f

# Database/Data Commands
load-data: ## Load and validate CSV data
	python load_data.py

validate-data: ## Validate CSV data integrity
	python -c "import pandas as pd; \
		ingredients = pd.read_csv('sample-data/ingredients.csv'); \
		recipes = pd.read_csv('sample-data/recipes.csv'); \
		print(f'Ingredients: {len(ingredients)} rows'); \
		print(f'Recipes: {len(recipes)} rows'); \
		print('Data validation passed!')"

init-db: ## Initialize database and load data
	python init_postgres.py
	python load_data.py

# Cleanup Commands
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -f test_nutrition_recipe.db test_recipe.db

clean-docker: ## Clean up Docker resources
	docker system prune -f
	docker volume prune -f
	docker image prune -f

# Security Commands
security-scan: ## Run security vulnerability scan
	pip install safety bandit
	safety check
	bandit -r main.py database.py load_data.py init_postgres.py

# Performance Commands
load-test: ## Run basic load test (requires httpx)
	python -c "import asyncio, httpx, time; \
		async def load_test(): \
			async with httpx.AsyncClient() as client: \
				start = time.time(); \
				tasks = [client.get('http://localhost:8000/health') for _ in range(100)]; \
				responses = await asyncio.gather(*tasks); \
				end = time.time(); \
				print(f'100 requests in {end-start:.2f}s'); \
				print(f'Success rate: {sum(1 for r in responses if r.status_code == 200)/len(responses)*100:.1f}%'); \
		asyncio.run(load_test())"

# Documentation Commands
docs: ## Generate API documentation
	@echo "API Documentation available at:"
	@echo "  Swagger UI: http://localhost:8000/docs"
	@echo "  ReDoc: http://localhost:8000/redoc"
	@echo ""
	@echo "Start the server with 'make run' to access documentation"

# CI/CD Commands
ci-test: ## Run CI test suite
	make lint
	make format-check
	make test-coverage
	make docker-build
	make test-docker

# Backup Commands
backup-data: ## Backup CSV data files
	mkdir -p backups
	cp sample-data/ingredients.csv backups/ingredients_$(shell date +%Y%m%d_%H%M%S).csv
	cp sample-data/recipes.csv backups/recipes_$(shell date +%Y%m%d_%H%M%S).csv
	@echo "Data backed up to backups/ directory"

# Monitoring Commands
health-check: ## Check application health
	@curl -f http://localhost:8000/health && echo "\nApplication is healthy!" || echo "\nApplication health check failed!"

metrics: ## Show basic application metrics
	@echo "Fetching application metrics..."
	@curl -s http://localhost:8000/health | python -m json.tool

# Environment Commands
env-check: ## Check environment configuration
	@echo "Python version: $(shell python --version)"
	@echo "Pip version: $(shell pip --version)"
	@echo "Docker version: $(shell docker --version 2>/dev/null || echo 'Docker not installed')"
	@echo "Docker Compose version: $(shell docker compose --version 2>/dev/null || echo 'Docker Compose not installed')"
	@echo ""
	@echo "Required CSV files:"
	@ls -la sample-data/ingredients.csv sample-data/recipes.csv 2>/dev/null || echo "CSV files not found in sample-data directory"

# Database management commands
postgres-shell: ## Connect to PostgreSQL shell
	docker compose exec postgres psql -U postgres -d nutritionrecipe

redis-cli: ## Connect to Redis CLI
	docker compose exec redis redis-cli

# Development workflow commands
dev-setup: ## Setup development environment
	make install
	make validate-data
	@echo "Development environment setup complete!"

dev-reset: ## Reset development environment
	make clean
	make clean-docker
	make install
	make up

# Quick start command
quickstart: install up ## Quick setup and run for development
	@echo "Waiting for services to start..."
	sleep 15
	@echo "Services should be ready at http://localhost:8000"
	@echo "API documentation: http://localhost:8000/docs"