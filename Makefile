.DEFAULT_GOAL := help

COMPOSE := docker compose
MODULE_1 := modules/01-oltp-mysql
MODULE_2 := modules/02-nosql-mongodb
# MYSQL_PWD keeps the password off the command line and silences the client's warning about it.
MYSQL_CLIENT := sh -c 'MYSQL_PWD="$$MYSQL_ROOT_PASSWORD" exec mysql --user=root'

.PHONY: help setup up admin down ps logs mysql mongo download load dump reset lint format

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

setup: ## Create the uv environment and a local .env
	uv sync
	@test -f .env || { cp .env.example .env; echo "Created .env, now replace its placeholder password."; }

up: ## Start MySQL and MongoDB and wait until they are healthy
	$(COMPOSE) up --detach --wait mysql mongo

admin: ## Start MySQL and phpMyAdmin
	$(COMPOSE) --profile admin up --detach --wait

down: ## Stop all services and keep the data
	$(COMPOSE) --profile admin down

ps: ## Show service status
	$(COMPOSE) --profile admin ps

logs: ## Follow MySQL logs
	$(COMPOSE) logs --follow mysql

mysql: ## Open a MySQL shell as root
	$(COMPOSE) exec mysql $(MYSQL_CLIENT)

mongo: ## Open a MongoDB shell as root
	$(COMPOSE) exec mongo sh -c 'exec mongosh --quiet --username root --password "$$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin'

download: ## Download the raw data for all modules
	bash $(MODULE_1)/scripts/download_data.sh
	bash $(MODULE_2)/scripts/download_data.sh

load: download ## Create the schema and load the OLTP data (safe to re-run)
	cat $(MODULE_1)/sql/01_create_database.sql \
		$(MODULE_1)/sql/02_create_sales_data.sql \
		$(MODULE_1)/sql/03_load_sales_data.sql \
		$(MODULE_1)/sql/04_create_index.sql | $(COMPOSE) exec -T mysql $(MYSQL_CLIENT)

dump: ## Export sales_data to sales_data.sql
	bash $(MODULE_1)/scripts/datadump.sh

reset: ## Stop all services and DELETE the database volume
	$(COMPOSE) --profile admin down --volumes

lint: ## Check imports and formatting without changing files
	uv run ruff check .
	uv run ruff format --check .

format: ## Fix imports and formatting
	uv run ruff check --fix .
	uv run ruff format .
