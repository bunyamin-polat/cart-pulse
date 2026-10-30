"""Connections to the ETL source and target, configured from .env."""

import os
from pathlib import Path

import mysql.connector
import psycopg2
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]

# Scripts can run from any directory, so the path is explicit.
load_dotenv(REPO_ROOT / ".env")


def connect_mysql():
    """Connect to the OLTP source, the sales database on the mysql-etl service."""
    return mysql.connector.connect(
        host="127.0.0.1",
        port=int(os.getenv("MYSQL_ETL_PORT", "3307")),
        user="root",
        password=os.environ["MYSQL_ROOT_PASSWORD"],
        database="sales",
    )


def connect_postgres():
    """Connect to the staging database of the PostgreSQL warehouse."""
    return psycopg2.connect(
        host="127.0.0.1",
        port=int(os.getenv("POSTGRES_PORT", "5434")),
        user="postgres",
        password=os.environ["POSTGRES_PASSWORD"],
        dbname="staging",
    )
