"""Shared access to the warehouse for the Spark jobs."""

import os

URL = "jdbc:postgresql://postgres:5432/warehouse"
PROPERTIES = {
    "user": "postgres",
    "password": os.environ["POSTGRES_PASSWORD"],
    "driver": "org.postgresql.Driver",
}


def read_table(spark, table):
    return spark.read.jdbc(URL, table, properties=PROPERTIES)


def replace_table(frame, table):
    """Replace the rows and keep the table, so its schema stays in the SQL files."""
    frame.write.jdbc(
        URL,
        table,
        mode="overwrite",
        properties={**PROPERTIES, "truncate": "true"},
    )
