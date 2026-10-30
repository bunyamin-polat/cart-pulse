.DEFAULT_GOAL := help

COMPOSE := docker compose
MODULE_1 := modules/01-oltp-mysql
MODULE_2 := modules/02-nosql-mongodb
MODULE_3 := modules/03-data-warehouse
MODULE_5 := modules/05-etl-airflow
PSQL := $(COMPOSE) exec -T postgres psql --username=postgres --set=ON_ERROR_STOP=1
# MYSQL_PWD keeps the password off the command line and silences the client's warning about it.
MYSQL_CLIENT := sh -c 'MYSQL_PWD="$$MYSQL_ROOT_PASSWORD" exec mysql --user=root'

.PHONY: help setup up admin down ps logs mysql mysql-etl mongo psql download load load-oltp load-catalog load-warehouse warehouse-schema warehouse-reports dump export-catalog reset lint format

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

setup: ## Create the uv environment and a local .env
	uv sync
	@test -f .env || { cp .env.example .env; echo "Created .env, now replace its placeholder password."; }

up: ## Start all databases and wait until they are healthy
	$(COMPOSE) up --detach --wait mysql mysql-etl mongo postgres

admin: ## Start all databases with phpMyAdmin and pgAdmin
	$(COMPOSE) --profile admin up --detach --wait

down: ## Stop all services and keep the data
	$(COMPOSE) --profile admin down

ps: ## Show service status
	$(COMPOSE) --profile admin ps

logs: ## Follow MySQL logs
	$(COMPOSE) logs --follow mysql

mysql: ## Open a MySQL shell as root
	$(COMPOSE) exec mysql $(MYSQL_CLIENT)

mysql-etl: ## Open a MySQL shell on the ETL source
	$(COMPOSE) exec mysql-etl $(MYSQL_CLIENT)

mongo: ## Open a MongoDB shell as root
	$(COMPOSE) exec mongo sh -c 'exec mongosh --quiet --username root --password "$$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin'

psql: ## Open a PostgreSQL shell
	$(COMPOSE) exec postgres psql --username=postgres

download: ## Download the raw data for all modules
	bash $(MODULE_1)/scripts/download_data.sh
	bash $(MODULE_2)/scripts/download_data.sh
	bash $(MODULE_3)/scripts/download_data.sh
	bash $(MODULE_5)/scripts/download_data.sh

load: load-oltp load-catalog load-warehouse ## Load all data (safe to re-run)

load-oltp: download ## Create the schema and load the OLTP data
	cat $(MODULE_1)/sql/01_create_database.sql \
		$(MODULE_1)/sql/02_create_sales_data.sql \
		$(MODULE_1)/sql/03_load_sales_data.sql \
		$(MODULE_1)/sql/04_create_index.sql | $(COMPOSE) exec -T mysql $(MYSQL_CLIENT)

load-catalog: download ## Load the product catalog into MongoDB
	bash $(MODULE_2)/scripts/load_catalog.sh

warehouse-schema: ## Create the staging database and star schema (safe to re-run)
	$(PSQL) < $(MODULE_3)/sql/01_create_database.sql
	$(PSQL) --dbname=staging < $(MODULE_3)/sql/02_create_schema.sql

load-warehouse: download warehouse-schema ## Rebuild the reporting tables and the MQT
	$(PSQL) < $(MODULE_3)/sql/03_create_reporting_database.sql
	$(PSQL) --dbname=Test1 < $(MODULE_3)/sql/04_load_reporting_data.sql
	$(PSQL) --dbname=Test1 < $(MODULE_3)/sql/05_create_mqt.sql

warehouse-reports: ## Run the warehouse analytics queries
	$(PSQL) --dbname=Test1 < $(MODULE_3)/sql/06_analytics_queries.sql

dump: ## Export sales_data to sales_data.sql
	bash $(MODULE_1)/scripts/datadump.sh

export-catalog: ## Export the catalog to electronics.csv
	bash $(MODULE_2)/scripts/export_catalog.sh

reset: ## Stop all services and DELETE the database volume
	$(COMPOSE) --profile admin down --volumes

lint: ## Check imports and formatting without changing files
	uv run ruff check .
	uv run ruff format --check .

format: ## Fix imports and formatting
	uv run ruff check --fix .
	uv run ruff format .
