"""Incremental load of orders from MySQL into the warehouse."""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta

from cartpulse.warehouse import copy_rows, record_load

SOURCE = "orders"
BATCH_SIZE = 10_000
INITIAL_WATERMARK = datetime(2000, 1, 1)
COLUMNS = (
    "order_id",
    "order_date",
    "country",
    "category",
    "amount",
    "status",
    "updated_at",
)
UPDATED_AT = COLUMNS.index("updated_at")

EXTRACT_QUERY = f"""
    SELECT {", ".join(COLUMNS)}
    FROM orders
    WHERE updated_at >= %s
    ORDER BY updated_at, order_id
"""

# Only rows that really changed count, so re-reading the lookback window is harmless.
UPSERT_QUERY = f"""
    INSERT INTO staging.orders ({", ".join(COLUMNS)})
    SELECT {", ".join(COLUMNS)} FROM incoming
    ON CONFLICT (order_id) DO UPDATE SET
        order_date = EXCLUDED.order_date,
        country = EXCLUDED.country,
        category = EXCLUDED.category,
        amount = EXCLUDED.amount,
        status = EXCLUDED.status,
        updated_at = EXCLUDED.updated_at,
        loaded_at = now()
    WHERE staging.orders.updated_at IS DISTINCT FROM EXCLUDED.updated_at
"""


@dataclass(frozen=True)
class SyncResult:
    rows_extracted: int
    rows_changed: int
    high_water_mark: datetime


def get_watermark(cursor):
    """Return how far the warehouse has read, or the start of time on a first run."""
    cursor.execute(
        "SELECT high_water_mark FROM etl.watermarks WHERE source = %s", (SOURCE,)
    )
    row = cursor.fetchone()
    return row[0] if row else INITIAL_WATERMARK


def save_watermark(cursor, high_water_mark):
    cursor.execute(
        """
        INSERT INTO etl.watermarks (source, high_water_mark)
        VALUES (%s, %s)
        ON CONFLICT (source) DO UPDATE SET
            high_water_mark = EXCLUDED.high_water_mark,
            updated_at = now()
        """,
        (SOURCE, high_water_mark),
    )


def read_batches(connection, since):
    """Yield source rows changed since the given time, oldest change first."""
    with closing(connection.cursor()) as cursor:
        cursor.execute(EXTRACT_QUERY, (since,))
        while batch := cursor.fetchmany(BATCH_SIZE):
            yield batch


def sync(source, target, lookback_seconds):
    """Copy changed orders into staging and move the watermark in one transaction.

    The lookback re-reads a short window, because a transaction that committed late can
    carry an earlier updated_at than rows that were already read. A failure rolls back
    both the rows and the watermark, so the next run retries the same window.
    """
    with target, target.cursor() as cursor:
        watermark = get_watermark(cursor)
        since = watermark - timedelta(seconds=lookback_seconds)

        cursor.execute(
            """
            CREATE TEMP TABLE incoming (LIKE staging.orders INCLUDING DEFAULTS)
            ON COMMIT DROP
            """
        )

        rows_extracted = 0
        for batch in read_batches(source, since):
            copy_rows(cursor, "incoming", COLUMNS, batch)
            rows_extracted += len(batch)
            watermark = max(watermark, batch[-1][UPDATED_AT])

        cursor.execute(UPSERT_QUERY)
        rows_changed = cursor.rowcount

        save_watermark(cursor, watermark)
        record_load(cursor, SOURCE, rows_extracted, rows_changed)

    return SyncResult(rows_extracted, rows_changed, watermark)
