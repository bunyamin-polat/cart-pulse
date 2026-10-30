# CartPulse Data Platform

An end-to-end e-commerce data platform that takes retail transactions from an OLTP database to warehouse analytics and sales forecasting.

[![CI](https://github.com/bunyamin-polat/cart-pulse/actions/workflows/ci.yml/badge.svg)](https://github.com/bunyamin-polat/cart-pulse/actions/workflows/ci.yml)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-2.10-017CEE?logo=apacheairflow&logoColor=white)
![Spark](https://img.shields.io/badge/Spark-4.2-E25A1C?logo=apachespark&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Ruff](https://img.shields.io/badge/code%20style-Ruff-D7FF64?logo=ruff&logoColor=black)
![License](https://img.shields.io/badge/license-MIT-green)

## Architecture

```mermaid
flowchart LR
    web[Website] --> mysql[(MySQL<br/>transactions)]
    web --> mongo[(MongoDB<br/>catalog)]
    web --> log[Web server log]
    mysql --> etl[Python ETL]
    etl --> pg[(PostgreSQL<br/>star schema)]
    pg --> spark[Spark ML<br/>forecasting]
    log --> airflow[Airflow DAG]
    airflow --> archive[weblog.tar]
```

Each module uses the dataset of its course lab, so the modules run independently. See [docs/architecture.md](docs/architecture.md) for the data flow and design rationale.

## Modules

| # | Module | Stack | Status |
| --- | ------ | ----- | ------ |
| 1 | [OLTP database](modules/01-oltp-mysql/README.md) | MySQL | ✅ Done |
| 2 | [NoSQL product catalog](modules/02-nosql-mongodb/README.md) | MongoDB | ✅ Done |
| 3 | [Data warehouse and reporting](modules/03-data-warehouse/README.md) | PostgreSQL | ✅ Done |
| 4 | [ETL pipelines](modules/04-etl-airflow/README.md) | Python, Airflow | ✅ Done |
| 5 | [Sales projections](modules/05-spark-ml/README.md) | Spark ML | ✅ Done |

### Highlights

- MySQL 8.0 runs in Docker Compose with a health check and a non-root user
- A single command loads 2,605 transactions, 438 catalog documents and 300,000 warehouse sales, and is safe to re-run
- A `ts` index supports time-based incremental exports
- `datadump.sh` backups are verified by restoring every row
- MongoDB stores products with different attributes in one collection
- A PostgreSQL star schema answers reports with `GROUPING SETS`, `ROLLUP`, `CUBE` and a materialized view
- A Python ETL copies only new rows, and a second run moves nothing
- An Airflow DAG processes the web server log every day
- Spark jobs analyze search terms and forecast sales, with a backtest against a plain average
- CI runs linting and unit tests on every push, and an integration workflow tests the ETL on real databases

## Quick start

Requires [Docker](https://docs.docker.com/get-docker/), [uv](https://docs.astral.sh/uv/) and `make`.

```bash
git clone https://github.com/bunyamin-polat/cart-pulse.git
cd cart-pulse

make setup   # create the Python environment and .env
```

Replace the placeholder passwords in `.env` before the first start, because each database stores its password when its volume is created.

```bash
make up      # start all databases and wait until they are healthy
make load    # download the data, create the schemas and load them
```

Then try the pipelines:

```bash
make warehouse-reports   # run the warehouse analytics queries
make run-etl             # copy new rows from the ETL source to the warehouse
make airflow             # start Apache Airflow
make spark-build         # build the Spark image
make spark-forecast      # train the sales model and forecast 2023
```

Run `make` to list every command. `make down` stops the services and keeps the data. `make reset` deletes every data volume.

## Project structure

```text
.
├── docker-compose.yml      Service definitions
├── Makefile                Common commands
├── pyproject.toml          Python tooling (uv, Ruff)
├── .env.example            Configuration template
├── .github/workflows/      CI and integration tests
├── docs/                   Architecture notes and images
├── tests/                  Unit tests
└── modules/
    ├── 01-oltp-mysql/
    │   ├── sql/            Database, schema, load and index statements
    │   ├── scripts/        Data download and dump scripts
    │   └── data/           Downloaded files (git-ignored)
    ├── 02-nosql-mongodb/
    ├── 03-data-warehouse/
    ├── 04-etl-airflow/
    └── 05-spark-ml/
```

## Development

Python tooling is managed with uv. Ruff handles both import sorting (isort rules) and formatting (Black-compatible).

```bash
make lint     # check without changing files
make format   # apply fixes
make test     # run the unit tests
```

CI runs linting, shell checks, Compose validation and unit tests on every push. The integration workflow starts real MySQL and PostgreSQL services and runs the ETL twice. It runs weekly and on demand, because it downloads the course data.

## Acknowledgment

This project is based on the capstone of the [IBM Data Engineering Professional Certificate](https://www.coursera.org/professional-certificates/ibm-data-engineer). The original lab runs in the IBM Cloud IDE, while this version runs locally with Docker Compose.

## License

[MIT](LICENSE)
