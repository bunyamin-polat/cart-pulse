"""Load the sample data into the source systems and simulate new business days.

The sample sales cover 2019 to 2021. December 2021 is held back, so `next-day` can
replay it one day at a time and give the pipeline real new orders to pick up.
"""

import argparse
import csv
import json
from contextlib import closing
from datetime import date, timedelta

from cartpulse.config import Settings
from cartpulse.connections import connect_mongo, connect_mysql

HISTORY_END = date(2021, 11, 30)
BATCH_SIZE = 5_000
CANCELLATIONS_PER_DAY = 5
INSERT_ORDER = """
    INSERT INTO orders (order_id, order_date, country, category, amount)
    VALUES (%s, %s, %s, %s, %s)
"""


def read_lookup(path, key, value):
    # utf-8-sig removes the byte order mark that DimCountry.csv starts with.
    with path.open(encoding="utf-8-sig", newline="") as file:
        return {row[key]: row[value] for row in csv.DictReader(file)}


def read_sales(data_dir):
    """Join the sample files into rows that look like the orders table."""
    dates = read_lookup(data_dir / "DimDate.csv", "dateid", "date")
    countries = read_lookup(data_dir / "DimCountry.csv", "countryid", "country")
    categories = read_lookup(data_dir / "DimCategory.csv", "categoryid", "category")

    with (data_dir / "FactSales.csv").open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            yield (
                int(row["orderid"]),
                date.fromisoformat(dates[row["dateid"]]),
                countries[row["countryid"]],
                categories[row["categoryid"]],
                int(row["amount"]),
            )


def insert_orders(connection, rows):
    """Insert rows in batches and return how many were written."""
    written = 0
    with closing(connection.cursor()) as cursor:
        batch = []
        for row in rows:
            batch.append(row)
            if len(batch) == BATCH_SIZE:
                cursor.executemany(INSERT_ORDER, batch)
                written += len(batch)
                batch = []
        if batch:
            cursor.executemany(INSERT_ORDER, batch)
            written += len(batch)
    connection.commit()
    return written


def seed_orders(settings):
    """Replace the orders table with the sales up to the end of the history."""
    with closing(connect_mysql(settings)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("TRUNCATE TABLE orders")
        rows = (r for r in read_sales(settings.data_dir) if r[1] <= HISTORY_END)
        written = insert_orders(connection, rows)
    print(f"Seeded {written} orders up to {HISTORY_END}")


def seed_catalog(settings):
    """Replace the catalog collection with the sample products."""
    path = settings.data_dir / "catalog.json"
    with path.open(encoding="utf-8") as file:
        documents = [json.loads(line) for line in file if line.strip()]

    with closing(connect_mongo(settings)) as client:
        products = client.cartpulse.products
        products.drop()
        products.insert_many(documents)
        products.create_index("type")
    print(f"Seeded {len(documents)} catalog products")


def next_day(settings):
    """Add the next day of held-back orders and cancel a few of the newest ones."""
    with closing(connect_mysql(settings)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT MAX(order_date) FROM orders")
            day = cursor.fetchone()[0] + timedelta(days=1)

        rows = (r for r in read_sales(settings.data_dir) if r[1] == day)
        written = insert_orders(connection, rows)
        if not written:
            print(f"No sample orders left after {day - timedelta(days=1)}")
            return

        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                UPDATE orders SET status = 'cancelled'
                WHERE order_date = %s AND status = 'completed'
                ORDER BY order_id
                LIMIT %s
                """,
                (day, CANCELLATIONS_PER_DAY),
            )
            cancelled = cursor.rowcount
        connection.commit()
    print(f"Added {written} orders for {day} and cancelled {cancelled}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("all", "next-day"))
    command = parser.parse_args().command

    settings = Settings()
    if command == "all":
        seed_orders(settings)
        seed_catalog(settings)
    else:
        next_day(settings)


if __name__ == "__main__":
    main()
