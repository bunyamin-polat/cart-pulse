"""The daily pipeline. Airflow runs these steps, and so does `make pipeline`."""

import logging
from contextlib import closing

from cartpulse import catalog, orders, quality, web_traffic
from cartpulse.config import Settings
from cartpulse.connections import connect_mongo, connect_mysql, connect_postgres
from cartpulse.warehouse import run_sql_file

log = logging.getLogger(__name__)


def prepare_warehouse():
    with closing(connect_postgres(Settings())) as target:
        run_sql_file(target, "01_schema.sql")
        run_sql_file(target, "02_marts.sql")


def load_orders():
    settings = Settings()
    with (
        closing(connect_mysql(settings)) as source,
        closing(connect_postgres(settings)) as target,
    ):
        result = orders.sync(source, target, settings.watermark_lookback_seconds)
    log.info("Orders: %s read, %s changed", result.rows_extracted, result.rows_changed)


def load_catalog():
    settings = Settings()
    with (
        closing(connect_mongo(settings)) as client,
        closing(connect_postgres(settings)) as target,
    ):
        products = catalog.sync(client.cartpulse.products, target)
    log.info("Catalog: %s products", products)


def load_web_traffic():
    settings = Settings()
    with closing(connect_postgres(settings)) as target:
        parsed = web_traffic.sync(
            settings.data_dir / "accesslog.txt", target, settings.excluded_ips
        )
    log.info(
        "Web traffic: %s requests, %s excluded, %s malformed",
        len(parsed.rows),
        parsed.excluded,
        parsed.malformed,
    )


def build_warehouse():
    with closing(connect_postgres(Settings())) as target:
        run_sql_file(target, "03_build_dimensions.sql")
        run_sql_file(target, "04_build_facts.sql")


def check_quality():
    settings = Settings()
    with (
        closing(connect_mysql(settings)) as source,
        closing(connect_postgres(settings)) as target,
    ):
        quality.assert_quality(source, target)
    log.info("Quality checks passed")


def refresh_marts():
    with closing(connect_postgres(Settings())) as target:
        run_sql_file(target, "05_refresh_marts.sql")


STEPS = (
    prepare_warehouse,
    load_orders,
    load_catalog,
    load_web_traffic,
    build_warehouse,
    check_quality,
    refresh_marts,
)


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for step in STEPS:
        log.info("Running %s", step.__name__)
        step()


if __name__ == "__main__":
    main()
