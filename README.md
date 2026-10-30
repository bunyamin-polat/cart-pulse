# CartPulse Data Platform

An end-to-end e-commerce data platform that takes retail transactions from an OLTP database to warehouse analytics, dashboards and sales forecasting.

![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-planned-47A248?logo=mongodb&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-planned-4169E1?logo=postgresql&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-planned-017CEE?logo=apacheairflow&logoColor=white)
![Spark](https://img.shields.io/badge/Spark-planned-E25A1C?logo=apachespark&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Ruff](https://img.shields.io/badge/code%20style-Ruff-D7FF64?logo=ruff&logoColor=black)
![License](https://img.shields.io/badge/license-MIT-green)

## Architecture

```mermaid
flowchart LR
    web[Website] --> mysql[(MySQL<br/>transactions)]
    web --> mongo[(MongoDB<br/>catalog)]
    mysql --> airflow[Airflow ETL]
    mongo --> airflow
    airflow --> pg[(PostgreSQL<br/>star schema)]
    pg --> bi[BI dashboards]
    pg --> spark[Spark ML<br/>forecasting]
```

## Roadmap

| # | Module | Stack | Status |
| --- | ------ | ----- | ------ |
| 1 | OLTP database | MySQL | 🚧 In progress |
| 2 | NoSQL product catalog | MongoDB | ⏳ Planned |
| 3 | Data warehouse and reporting | PostgreSQL | ⏳ Planned |
| 4 | BI dashboard | Looker Studio or Cognos Analytics | ⏳ Planned |
| 5 | ETL pipelines | Python, Airflow | ⏳ Planned |
| 6 | Sales projections | Spark ML | ⏳ Planned |

### Module 1 progress

- ✅ MySQL 8.0 running in Docker Compose with a health check
- ✅ `sales` database and `sales_data` table
- ✅ Scripted download and idempotent bulk load of 2,605 transactions
- ✅ `ts` index on `timestamp` for time-based incremental exports
- ✅ `datadump.sh` backup script, verified with a restore of all rows
- ⏳ Module documentation

## Quick start

Requires [Docker](https://docs.docker.com/get-docker/), [uv](https://docs.astral.sh/uv/) and `make`.

```bash
git clone https://github.com/bunyamin-polat/cart-pulse.git
cd cart-pulse

make setup   # create the Python environment and .env
```

Replace the placeholder password in `.env` before the first start, because MySQL stores it when the database volume is created.

```bash
make up      # start MySQL and wait until it is healthy
make load    # download the data, create the schema and load it
make mysql   # open a MySQL shell
make dump    # export sales_data to a SQL file
```

Run `make` to list every command. `make down` stops the services and keeps the data. `make reset` also deletes the database volume.

## Project structure

```text
.
├── docker-compose.yml      Service definitions
├── Makefile                Common commands
├── pyproject.toml          Python tooling (uv, Ruff)
├── .env.example            Configuration template
├── docs/                   Architecture notes and images
└── modules/
    ├── 01-oltp-mysql/
    │   ├── sql/            Database, schema, load and index statements
    │   ├── scripts/        Data download and dump scripts
    │   └── data/           Downloaded files (git-ignored)
    ├── 02-nosql-mongodb/
    ├── 03-data-warehouse/
    ├── 04-bi-dashboard/
    ├── 05-etl-airflow/
    └── 06-spark-ml/
```

## Development

Python tooling is managed with uv. Ruff handles both import sorting (isort rules) and formatting (Black-compatible).

```bash
make lint     # check without changing files
make format   # apply fixes
```

## Acknowledgment

This project is based on the capstone of the [IBM Data Engineering Professional Certificate](https://www.coursera.org/professional-certificates/ibm-data-engineer). The original lab runs in the IBM Cloud IDE, while this version runs locally with Docker Compose.

## License

[MIT](LICENSE)
