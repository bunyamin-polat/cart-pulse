# Module 2: Product Catalog with MongoDB

## Goal

Store the CartPulse product catalog in a document database, query it, and export it in a form other systems can consume.

## Run it

From the repository root:

```bash
make setup            # then replace the placeholder passwords in .env
make up
make load-catalog
make export-catalog
```

`make load-catalog` is safe to re-run. It leaves the same 438 documents and the same indexes every time.

## Design decisions

### Why a document database

Products do not share one shape. In this dataset, laptops have `ram` and `hard disk` fields, while smart phones and televisions do not. A relational table would need columns that stay empty for most products, or a new table for each product type. A document stores only the fields that apply to it.

| MySQL | MongoDB | In this module |
| --- | --- | --- |
| Database | Database | `catalog` |
| Table | Collection | `electronics` |
| Row | Document | One product |
| Column | Field | `model` |

### Why an index on `type`

Every report in this module filters by `type`. The index lets MongoDB jump to matching documents without reading the whole collection. The catalog is read far more often than it changes, so the cost on writes is a good trade.

### Known trade-offs

- **Authentication uses `root`.** This keeps the local setup simple. Production jobs would use a dedicated account with least privilege.
- **`_id` is generated at load time.** The source file has no IDs, so `--drop` plus re-import produces new `ObjectId` values. Anything that needs stable IDs should use a natural key such as a product SKU.

## Steps

### Exercise 1: Check the lab environment

Start MongoDB with `make up`. `mongoimport` and `mongoexport` ship with the Docker image, so nothing else needs to be installed. `make download` fetches `catalog.json`.

Inspection of the file showed newline-delimited JSON with one document per line, no `_id` fields, and a field name containing a space (`screen size`). `wc -l` reports 437 because the last line has no trailing newline. The file holds 438 documents.

### Exercise 2: Working with MongoDB

- **Task 1:** Import `catalog.json` into `catalog.electronics` with [load_catalog.sh](scripts/load_catalog.sh).
- **Task 2:** List databases with `show dbs`.
- **Task 3:** List collections with `show collections`.
- **Task 4:** Create the index with `db.electronics.createIndex({ type: 1 })`.
- **Task 5:** Count laptops.

  ```javascript
  db.electronics.countDocuments({ type: "laptop" })
  ```

- **Task 6:** Count smart phones with a 6-inch screen.

  ```javascript
  db.electronics.countDocuments({ type: "smart phone", "screen size": 6 })
  ```

- **Task 7:** Find the average screen size of smart phones.

  ```javascript
  db.electronics.aggregate([
    { $match: { type: "smart phone" } },
    { $group: { _id: "$type", averageScreenSize: { $avg: "$screen size" } } }
  ])
  ```

- **Task 8:** Export `_id`, `type` and `model` to `electronics.csv` with [export_catalog.sh](scripts/export_catalog.sh).

## Results

| Check | Result |
| --- | --- |
| Documents imported | 438, with 0 failures |
| Laptops | 389 |
| Televisions | 25 |
| Smart phones | 24 |
| 6-inch smart phones | 8 |
| Average smart phone screen | 6 inches |
| Indexes | `_id_` and `type_1` |
| CSV export | 438 records plus a header row |

## Key learnings

- **Schema flexibility solves a real problem.** Products with different attributes fit naturally into one collection.
- **Flexible does not mean schema-free.** Queries still depend on exact field names and values, so `smartphone` returns 0 where `smart phone` returns 24.
- **Idempotency needs extra care without natural keys.** With no `_id` in the source, a repeated import duplicates data unless the collection is dropped first.
- **Aggregation pipelines read like SQL in steps.** `$match` maps to `WHERE`, and `$group` maps to `GROUP BY`.
- **CSV needs a fixed shape.** Exporting documents to CSV forces an explicit field list, which is a small preview of the warehouse work ahead.
