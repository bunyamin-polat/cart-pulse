"""Copy new sales rows from the MySQL source to the PostgreSQL warehouse."""

from contextlib import closing

from connections import connect_mysql, connect_postgres
from psycopg2.extras import execute_values


def get_last_rowid(connection):
    """Return the highest rowid in the warehouse, or 0 when the table is empty."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(rowid), 0) FROM sales_data")
        return cursor.fetchone()[0]


def get_latest_records(connection, rowid):
    """Return every source row newer than rowid, oldest first."""
    query = """
        SELECT rowid, product_id, customer_id, quantity
        FROM sales_data
        WHERE rowid > %s
        ORDER BY rowid
    """
    with closing(connection.cursor()) as cursor:
        cursor.execute(query, (rowid,))
        return cursor.fetchall()


def insert_records(connection, records):
    """Insert all records in one transaction, so a failure leaves no partial load."""
    if not records:
        return

    # price and timeestamp are absent from the source and fall back to column defaults.
    query = """
        INSERT INTO sales_data (rowid, product_id, customer_id, quantity)
        VALUES %s
    """
    with connection, connection.cursor() as cursor:
        execute_values(cursor, query, records)


def main():
    with closing(connect_mysql()) as source, closing(connect_postgres()) as target:
        last_row_id = get_last_rowid(target)
        print("Last row id on production datawarehouse = ", last_row_id)

        new_records = get_latest_records(source, last_row_id)
        print("New rows on staging datawarehouse = ", len(new_records))

        insert_records(target, new_records)
        print("New rows inserted into production datawarehouse = ", len(new_records))


if __name__ == "__main__":
    main()
