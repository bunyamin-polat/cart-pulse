"""Confirm that Python can reach both databases before running the ETL."""

from contextlib import closing

from connections import connect_mysql, connect_postgres

QUERY = "SELECT COUNT(*), MAX(rowid) FROM sales_data"


def report(name, connection):
    with closing(connection), closing(connection.cursor()) as cursor:
        cursor.execute(QUERY)
        count, last_rowid = cursor.fetchone()
    print(f"{name}: connected, {count} rows, last rowid {last_rowid}")


report("MySQL", connect_mysql())
report("PostgreSQL", connect_postgres())
