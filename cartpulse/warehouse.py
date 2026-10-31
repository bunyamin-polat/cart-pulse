"""Helpers for writing to the warehouse and running its SQL files."""

import csv
import io

from cartpulse.config import REPO_ROOT

SQL_DIR = REPO_ROOT / "sql" / "warehouse"


def run_sql_file(connection, name):
    """Run one SQL file in a single transaction, so it applies fully or not at all."""
    with connection, connection.cursor() as cursor:
        cursor.execute((SQL_DIR / name).read_text())


def copy_rows(cursor, table, columns, rows):
    """Bulk load rows with COPY, which is far faster than row-by-row inserts."""
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    buffer.seek(0)
    cursor.copy_expert(
        f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)", buffer
    )


def record_load(
    cursor, source, rows_extracted, rows_changed, rows_excluded=0, rows_rejected=0
):
    cursor.execute(
        """
        INSERT INTO etl.load_audit (
            source, rows_extracted, rows_changed, rows_excluded, rows_rejected
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (source, rows_extracted, rows_changed, rows_excluded, rows_rejected),
    )
