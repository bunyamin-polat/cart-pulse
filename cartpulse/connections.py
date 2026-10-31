"""Connections to the source systems and the warehouse."""

import mysql.connector
import psycopg2
from pymongo import MongoClient


def connect_mysql(settings):
    """Connect to the orders database. Sessions use UTC to match the watermark."""
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user="cartpulse",
        password=settings.mysql_password,
        database="cartpulse",
        time_zone="+00:00",
    )


def connect_postgres(settings):
    """Connect to the warehouse. Sessions use UTC to match the watermark."""
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user="postgres",
        password=settings.postgres_password,
        dbname="warehouse",
        options="-c timezone=UTC",
    )


def connect_mongo(settings):
    return MongoClient(
        host=settings.mongo_host,
        port=settings.mongo_port,
        username="root",
        password=settings.mongo_password,
        authSource="admin",
    )
