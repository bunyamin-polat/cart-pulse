.DEFAULT_GOAL := help

COMPOSE := docker compose
MODULE_1 := modules/01-oltp-mysql
MODULE_2 := modules/02-nosql-mongodb
MODULE_3 := modules/03-data-warehouse
MODULE_4 := modules/04-etl-airflow
MODULE_5 := modules/05-spark-ml
SPARK_SUBMIT := $(COMPOSE) --profile spark run --rm spark /opt/spark/bin/spark-submit --master 'local[*]' --conf spark.ui.enabled=false
PSQL := $(COMPOSE) exec -T postgres psql --username=postgres --set=ON_ERROR_STOP=1
# MYSQL_PWD keeps the password off the command line and silences the client's warning about it.
MYSQL_CLIENT := sh -c 'MYSQL_PWD="$$MYSQL_ROOT_PASSWORD" exec mysql --user=root'

.PHONY: help setup up admin airflow airflow-password spark-build spark-search spark-persistence spark-forecast down ps logs mysql mysql-etl mongo psql download load load-oltp load-catalog load-warehouse load-etl run-etl warehouse-schema warehouse-reports dump export-catalog reset lint format test

help: ## Show available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'

setup: ## Create the uv environment and a local .env
	uv sync
	@test -f .env || { cp .env.example .env; echo "Created .env, now replace its placeholder passwords."; }

up: ## Start all databases and wait until they are healthy
	$(COMPOSE) up --detach --wait mysql mysql-etl mongo postgres

admin: ## Start all databases with phpMyAdmin and pgAdmin
	$(COMPOSE) --profile admin up --detach --wait

airflow: ## Start Apache Airflow
	$(COMPOSE) --profile airflow up --detach --wait airflow

spark-build: ## Build the Spark image
	$(COMPOSE) --profile spark build spark

spark-search: download ## Analyze the search terms
	$(SPARK_SUBMIT) jobs/search_terms.py

spark-persistence: ## Train, save and reload a small example model
	$(SPARK_SUBMIT) jobs/model_persistence.py

spark-forecast: ## Train the sales model on warehouse data and forecast 2023
	$(PSQL) --dbname=Test1 --quiet < $(MODULE_5)/sql/export_monthly_sales.sql > $(MODULE_5)/data/monthly_sales.csv
	$(SPARK_SUBMIT) jobs/sales_forecast.py

airflow-password: ## Show the generated Airflow admin password
	$(COMPOSE) exec airflow sh -c 'cat /opt/airflow/standalone_admin_password.txt; echo'

down: ## Stop all services and keep the data
	$(COMPOSE) --profile admin --profile airflow --profile spark down

ps: ## Show service status
	$(COMPOSE) --profile admin --profile airflow --profile spark ps

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
	bash $(MODULE_4)/scripts/download_data.sh
	bash $(MODULE_5)/scripts/download_data.sh

load: load-oltp load-catalog load-warehouse load-etl ## Load all data (safe to re-run)

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

load-etl: download warehouse-schema ## Reset the ETL source and target to their initial state
	cat $(MODULE_4)/sql/00_reset_source.sql $(MODULE_4)/data/sales.sql \
		| $(COMPOSE) exec -T mysql-etl $(MYSQL_CLIENT)
	$(PSQL) --dbname=staging < $(MODULE_4)/sql/01_create_sales_data.sql
	$(PSQL) --dbname=staging < $(MODULE_4)/sql/02_load_sales_csv.sql

run-etl: ## Copy new rows from the ETL source to the warehouse
	uv run python $(MODULE_4)/etl/automation.py

dump: ## Export sales_data to sales_data.sql
	bash $(MODULE_1)/scripts/datadump.sh

export-catalog: ## Export the catalog to electronics.csv
	bash $(MODULE_2)/scripts/export_catalog.sh

reset: ## Stop all services and DELETE every data volume
	$(COMPOSE) --profile admin --profile airflow --profile spark down --volumes

lint: ## Check imports and formatting without changing files
	uv run ruff check .
	uv run ruff format --check .

test: ## Run the unit tests
	uv run pytest

format: ## Fix imports and formatting
	uv run ruff check --fix .
	uv run ruff format .
