# Module 1: OLTP Database with MySQL

## Goal

Build the transactional database behind the CartPulse storefront. It records every sale with low write latency and acts as the source for the warehouse pipeline in Module 5.

## Run it

From the repository root:

```bash
make setup   # then replace the placeholder password in .env
make up
make load-oltp
make dump
```

`make load-oltp` is safe to re-run. It leaves the same 2,605 rows and one `ts` index every time.

## Design decisions

### Data types

| Column | Type | Why |
| --- | --- | --- |
| `product_id` | `INT UNSIGNED` | IDs are never negative, and a fixed 4-byte integer is compact and fast to compare. |
| `customer_id` | `INT UNSIGNED` | Same reasoning as `product_id`. |
| `price` | `DECIMAL(10, 2)` | Exact arithmetic. Binary floats introduce rounding errors in money. |
| `quantity` | `SMALLINT UNSIGNED` | 65,535 units per line is more than enough, at 2 bytes per row. |
| `timestamp` | `DATETIME` | Stored as written, with no time zone conversion and no 2038 limit. |

Every column is `NOT NULL`, because a sale with a missing field is a data quality problem that should fail at write time.

### Why an index on `timestamp`

Module 4 will export new sales to the warehouse every day by filtering on time. A B-tree index lets those range queries avoid a full table scan as the table grows.

Each index also adds work to every `INSERT`, so this write-heavy table carries only the one index it needs. `make load-oltp` builds it after the bulk load, because building it once is cheaper than updating it row by row.

### OLTP vs OLAP

| | OLTP (this module) | OLAP (Module 3) |
| --- | --- | --- |
| Workload | Many small reads and writes | Few large analytical queries |
| Optimized for | Low latency and concurrent writes | Scans and aggregations |
| Schema | Normalized | Star schema |
| Indexing | Minimal | Designed around reporting |

### Known trade-offs

- **No primary key.** The course fixes these five columns, and no natural key exists because a customer can buy the same product again. InnoDB falls back to a hidden row ID. A production table would add a surrogate `sale_id`.
- **MySQL 8.0 is past end of life.** Support ended in April 2026. It is used here for parity with the course lab. A new production system would start on a current LTS release.
- **Root account.** Scripts connect as `root` for simplicity. Production jobs would use a dedicated account with least privilege.

## Steps

### Exercise 1: Check the lab environment

Start MySQL with `make up`. The command waits for the health check to pass. The container runs as the non-root `mysql` user, and the data folder is mounted read-only.

### Exercise 2: Design the OLTP database

- **Task 1:** Create the `sales` database with [01_create_database.sql](sql/01_create_database.sql).
- **Task 2:** Create the `sales_data` table with [02_create_sales_data.sql](sql/02_create_sales_data.sql).

### Exercise 3: Load the data

**Task 3:** Download `oltpdata.csv` with [download_data.sh](scripts/download_data.sh) and bulk load it with [03_load_sales_data.sql](sql/03_load_sales_data.sql).

Inspection before the load showed:

| Property | Value |
| --- | --- |
| Header row | None |
| Column order | Matches the table |
| Delimiter | Comma |
| Line ending | LF, with no newline after the last row |
| Date format | `YYYY-MM-DD HH:MM:SS` |

`wc -l` reports 2,604 because it counts newline characters and the final row has none. The file holds 2,605 records.

### Exercise 4: Set up admin tasks

- **Task 4:** Create the `ts` index with [04_create_index.sql](sql/04_create_index.sql). MySQL has no `CREATE INDEX IF NOT EXISTS`, so the script checks first.
- **Task 5:** List the indexes with `SHOW INDEX FROM sales.sales_data;`.
- **Task 6:** Export the table to `sales_data.sql` with [datadump.sh](scripts/datadump.sh). It uses `--single-transaction` to take a consistent snapshot without blocking writers.

## Results

| Check | Result |
| --- | --- |
| Rows loaded | 2,605, with 0 skipped and 0 warnings |
| Distinct products | 1,534 |
| Price range | 57 to 4,993 |
| Quantity range | 1 to 5 |
| Time range | 2020-09-05 16:20:03 to 17:03:27 |
| Index | `ts` on `timestamp` (BTREE) |
| Dump | 118 KB, restored to 2,605 rows in a separate database |
| Clean install | Passed from a fresh clone, including a second load |

The dataset covers about 43 minutes of sales, so later modules should not assume it spans multiple days.

## Key learnings

- **Choose types for the workload.** `DECIMAL` for money and compact integers matter when a table takes constant writes.
- **Indexes are a trade-off.** The `timestamp` index speeds up incremental exports and costs a little on every insert.
- **Inspect data before loading it.** Header, delimiter, line endings and date format decide how the load statement is written.
- **Counting lines is not counting records.** `wc -l` returned 2,604 for 2,605 rows because the file has no trailing newline.
- **Make every step safe to re-run.** Reproducible loads turned a fresh clone into a one-command setup.
- **Read the logs before changing config.** An unhealthy container traced back to the image entrypoint trying to `chown` a read-only mount. Running as the non-root `mysql` user fixed it and tightened security.
- **Verify backups by restoring them.** A dump file is only proven useful once it restores the expected row count.
