# Architecture

CartPulse moves retail data from operational stores into a warehouse that serves analytical reports and sales forecasting.

```mermaid
flowchart LR
    web[Website]

    subgraph sources[Operational stores]
        mysql[(MySQL<br/>sales transactions)]
        mongo[(MongoDB<br/>product catalog)]
        log[Web server log]
    end

    subgraph processing[Processing]
        etl[Python ETL<br/>incremental load]
        airflow[Airflow DAG<br/>daily log pipeline]
    end

    subgraph analytics[Analytics]
        pg[(PostgreSQL<br/>star schema)]
        spark[Spark ML<br/>sales forecasting]
        archive[weblog.tar]
    end

    web --> mysql
    web --> mongo
    web --> log
    mysql --> etl
    etl --> pg
    pg --> spark
    log --> airflow
    airflow --> archive
```

## Components

| Component | Role | Module | Status |
| --- | --- | --- | --- |
| MySQL | Records sales with low write latency | 1 | ✅ Built |
| MongoDB | Stores the flexible product catalog | 2 | ✅ Built |
| PostgreSQL | Holds fact and dimension tables for reporting | 3 | ✅ Built |
| Python ETL and Airflow | Copy new sales to the warehouse and process the web log | 4 | ✅ Built |
| Spark ML | Analyzes search terms and projects future sales | 5 | ✅ Built |

## Data flow

1. The website writes transactions to MySQL and reads product data from MongoDB.
2. A Python ETL job copies new sales from MySQL to PostgreSQL, using the highest `rowid` as a high-water mark.
3. Airflow runs a daily pipeline that extracts, filters and archives the web server log.
4. Reports and Spark ML read from the warehouse, so analytics never compete with live transactions.

Each module uses the dataset of its course lab, so the modules run independently. The catalog does not feed the warehouse yet, and Airflow does not schedule the Python ETL yet.

## Why separate stores

Each store fits one workload. MySQL handles concurrent writes, MongoDB handles product attributes that vary by category, and PostgreSQL handles analytical queries. Keeping analytics off the OLTP database protects checkout latency.

## Repository conventions

- Each module lives in its own folder under `modules/` with its own README.
- All services are defined in the root `docker-compose.yml`, and optional tools sit behind Compose profiles.
- The root `Makefile` is the single entry point for common tasks.
- Credentials live in a git-ignored `.env` file.
- Setup and load steps are safe to re-run.
- Raw data is downloaded by script and never committed.
