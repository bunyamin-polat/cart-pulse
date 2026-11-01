# Operations

## Services

| Service | Address | Started by |
| --- | --- | --- |
| MySQL | `127.0.0.1:3306` | `make up` |
| MongoDB | `127.0.0.1:27017` | `make up` |
| PostgreSQL | `127.0.0.1:5434` | `make up` |
| Airflow | <http://127.0.0.1:8088> | `make airflow` |

Spark has no running service. Each job starts a container and exits.

Ports come from `.env`. All of them are bound to localhost, and Airflow signs every local visitor in as an admin, so do not publish these ports.

## Running the pipeline

Under Airflow, `cartpulse_daily` runs every day at midnight UTC and retries a failed step twice. To run it now and wait for the result, use the Airflow page or:

```bash
make run-dag
```

Without Airflow, `make pipeline` runs the same steps in order. Do not run both at once.

## Checking a run

Latest loads:

```sql
SELECT * FROM etl.load_audit ORDER BY load_id DESC LIMIT 10;
```

How far the orders load has read:

```sql
SELECT * FROM etl.watermarks;
```

## When something fails

### A quality check failed

The marts keep their last good state, and the error names each failed check with its number of violations. Find the cause in `staging`, fix it in the source, and run the pipeline again. Corrected rows flow through because MySQL updates their `updated_at`.

### Reconciliation failed

`warehouse_matches_source` counts the orders that differ from MySQL. If the warehouse logic is sound, the usual cause is a change that committed outside the lookback window. Re-read a wider window to repair it:

```bash
CARTPULSE_WATERMARK_LOOKBACK_SECONDS=86400 make pipeline
```

Under Airflow, set the same variable on the service. If the check fails again, compare `orders` in MySQL with `staging.orders` and find the rows that differ.

A row that changes in MySQL between the load and the check can also raise this alarm. The next run clears it.

`catalog_matches_source` and `web_traffic_matches_log` mean a load did not match its source. Run the pipeline again, and check `rows_rejected` in `etl.load_audit` if the log check keeps failing.

### A load failed

Nothing was committed, so run it again. The watermark has not moved, and the next run reads the same window.

### MongoDB does not start

If the log says `Linux kernel versions 6.19 and newer has a known incompatibility`, the host kernel is in the range MongoDB blocks, 6.19 to 7.0.13. Containers share the host kernel, so changing the image does not help. Upgrade the kernel to 7.0.14 or later, or use one older than 6.19. Docker Desktop runs its own kernel, so updating Docker Desktop can also solve it.

### The log format changed

`load_web_traffic` stops when more than 1% of lines cannot be parsed. Update `LOG_LINE` in `cartpulse/web_traffic.py`.

### Rebuilding the warehouse from the sources

```bash
docker compose exec postgres psql --username=postgres --dbname=warehouse \
    -c "DROP SCHEMA etl, staging, dw, marts CASCADE"
make pipeline
```

The forecast and the search ranking are dropped too, so run `make forecast` and `make search-terms` afterwards.

## Backup and restore

`make backup` writes the orders table to `data/backups/`. The dump uses a consistent snapshot, so the store keeps taking orders while it runs.

To restore a backup:

```bash
docker compose exec -T mysql sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --user=root cartpulse' \
    < data/backups/orders_YYYYMMDDTHHMMSSZ.sql
```

The dump keeps each row's `updated_at`, so restored rows do not look like new changes. Orders written after the backup are lost from MySQL but stay in the warehouse, which fails the reconciliation check until the two agree.

MongoDB and the warehouse have no backup script: the catalog is sample data here, and the warehouse can be rebuilt from its sources.

## Resetting

`make down` stops everything and keeps the data. `make reset` also deletes every volume, including the databases and Airflow's history. `make demo` then rebuilds the platform from nothing.

`make seed` and `make demo` replace the orders and the catalog with the sample data, so do not run them on data you want to keep.

`make test-integration` is safe on a running platform. It starts a temporary Compose project with its own volumes and ports, and removes it when it finishes. It stops if another run is in progress.

Passwords are stored when a volume is created, so changing one in `.env` needs a `make reset`.

## Keeping up to date

All image versions are pinned in `docker-compose.yml` and the Dockerfiles, and Python packages are locked in `uv.lock`, so updates are always a deliberate change. Check an image with:

```bash
docker scout quickview cartpulse-spark:4.3.0
```

Current upstream images still report fixable issues in the libraries they bundle, so review the scan when you update, and before exposing anything beyond localhost.
