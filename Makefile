.DEFAULT_GOAL := help

COMPOSE := docker compose
SPARK_SUBMIT := $(COMPOSE) --profile spark run --rm spark spark-submit --master 'local[*]' --jars /opt/postgresql.jar --conf spark.ui.enabled=false
PSQL := $(COMPOSE) exec -T postgres psql --username=postgres --dbname=warehouse --set=ON_ERROR_STOP=1
ALL_PROFILES := --profile airflow --profile spark

.PHONY: help setup up down ps logs reset mysql mongo psql download seed pipeline next-day demo report backup airflow forecast search-terms lint format test test-integration

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'

setup: ## Create the Python environment and a local .env
	uv sync
	@test -f .env || { cp .env.example .env; echo "Created .env, now replace its placeholder passwords."; }

up: ## Start the databases and wait until they are healthy
	$(COMPOSE) up --detach --wait mysql mongo postgres

down: ## Stop all services and keep the data
	$(COMPOSE) $(ALL_PROFILES) down

ps: ## Show service status
	$(COMPOSE) $(ALL_PROFILES) ps

logs: ## Follow the logs of all running services
	$(COMPOSE) logs --follow

reset: ## Stop all services and DELETE every data volume
	$(COMPOSE) $(ALL_PROFILES) down --volumes

mysql: ## Open a shell on the orders database
	$(COMPOSE) exec mysql sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" exec mysql --user=cartpulse cartpulse'

mongo: ## Open a shell on the catalog database
	$(COMPOSE) exec mongo sh -c 'exec mongosh --quiet --username root --password "$$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin cartpulse'

psql: ## Open a shell on the warehouse
	$(COMPOSE) exec postgres psql --username=postgres --dbname=warehouse

download: ## Download the sample data
	bash scripts/download_data.sh

seed: download ## Replace the source systems with the sample data
	uv run python -m cartpulse.seed all

pipeline: ## Load the warehouse, check it and publish the marts
	uv run python -m cartpulse.pipeline

next-day: ## Simulate one business day of new and cancelled orders
	uv run python -m cartpulse.seed next-day

demo: up seed pipeline ## Run the whole flow from an empty system
	$(MAKE) next-day
	$(MAKE) pipeline
	$(MAKE) report

report: ## Print the main sales reports
	$(PSQL) --quiet < sql/reports/sales_reports.sql

backup: ## Write a backup of the orders table
	bash scripts/backup_oltp.sh

airflow: ## Start Apache Airflow
	$(COMPOSE) --profile airflow up --detach --wait --build airflow

forecast: ## Publish the sales forecast to the warehouse
	$(COMPOSE) --profile spark build spark
	$(SPARK_SUBMIT) jobs/sales_forecast.py

search-terms: download ## Publish the search term ranking to the warehouse
	$(COMPOSE) --profile spark build spark
	$(SPARK_SUBMIT) jobs/search_terms.py

lint: ## Check imports and formatting without changing files
	uv run ruff check .
	uv run ruff format --check .

format: ## Fix imports and formatting
	uv run ruff check --fix .
	uv run ruff format .

test: ## Run the unit tests
	uv run pytest

test-integration: ## Run the end-to-end tests in a temporary, separate stack
	bash scripts/run_integration_tests.sh
