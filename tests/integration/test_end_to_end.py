"""Run the real pipeline from sources to marts.

These tests erase the databases they connect to. Run them with `make test-integration`,
which starts a temporary stack with its own volumes and removes it afterwards.
"""

import os
from contextlib import closing

import pytest

from cartpulse import pipeline, quality, seed
from cartpulse.config import Settings
from cartpulse.connections import connect_mysql, connect_postgres

pytestmark = pytest.mark.integration


def warehouse_value(query):
    with closing(connect_postgres(Settings())) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]


def source_value(query):
    with closing(connect_mysql(Settings())) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]


def last_load():
    return warehouse_value(
        """
        SELECT rows_changed FROM etl.load_audit
        WHERE source = 'orders' ORDER BY load_id DESC LIMIT 1
        """
    )


def clear_warehouse():
    with closing(connect_postgres(Settings())) as connection:
        with connection, connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE etl.watermarks, etl.load_audit, staging.orders,
                    dw.fact_sales, dw.dim_country, dw.dim_category
                RESTART IDENTITY CASCADE
                """
            )


@pytest.fixture(scope="module")
def loaded_platform():
    if os.environ.get("CARTPULSE_TEST_STACK") != "1":
        pytest.fail("Use `make test-integration`, which runs on a separate stack")

    settings = Settings()
    pipeline.prepare_warehouse()
    clear_warehouse()
    seed.seed_orders(settings)
    seed.seed_catalog(settings)
    for step in pipeline.STEPS:
        step()


def test_first_run_loads_every_order(loaded_platform):
    orders = source_value("SELECT COUNT(*) FROM orders")

    assert warehouse_value("SELECT COUNT(*) FROM dw.fact_sales") == orders


def test_second_run_changes_nothing(loaded_platform):
    pipeline.load_orders()

    assert last_load() == 0


def test_marts_exclude_cancelled_orders_and_match_the_facts(loaded_platform):
    seed.next_day(Settings())
    for step in pipeline.STEPS:
        step()

    cancelled = warehouse_value(
        "SELECT COUNT(*) FROM dw.fact_sales WHERE status = 'cancelled'"
    )
    completed_total = warehouse_value(
        "SELECT SUM(amount) FROM dw.fact_sales WHERE status = 'completed'"
    )
    mart_total = warehouse_value(
        "SELECT SUM(total_sales) FROM marts.sales_by_year_country"
    )

    assert cancelled == seed.CANCELLATIONS_PER_DAY
    assert mart_total == completed_total


def test_new_day_loads_only_what_changed(loaded_platform):
    new_orders = source_value(
        """
        SELECT COUNT(*) FROM orders
        WHERE order_date = (SELECT MAX(order_date) FROM orders)
        """
    )

    assert last_load() == new_orders


def test_bad_data_keeps_the_last_good_reports(loaded_platform):
    settings = Settings()
    published = warehouse_value(
        "SELECT SUM(total_sales) FROM marts.sales_by_year_country"
    )

    with closing(connect_mysql(settings)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("UPDATE orders SET amount = -1 WHERE order_id = 1")
        connection.commit()

    pipeline.load_orders()
    pipeline.build_warehouse()
    with pytest.raises(quality.QualityCheckError, match="amounts_are_positive"):
        pipeline.check_quality()

    assert (
        warehouse_value("SELECT SUM(total_sales) FROM marts.sales_by_year_country")
        == published
    )

    with closing(connect_mysql(settings)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("UPDATE orders SET amount = 5190 WHERE order_id = 1")
        connection.commit()

    for step in pipeline.STEPS:
        step()

    assert (
        warehouse_value("SELECT SUM(total_sales) FROM marts.sales_by_year_country")
        == published
    )


def test_a_wrong_dimension_is_caught_and_rebuilt(loaded_platform):
    with closing(connect_postgres(Settings())) as connection:
        with connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE dw.fact_sales f SET country_key = (
                    SELECT MIN(country_key) FROM dw.dim_country
                    WHERE country_key <> f.country_key
                )
                WHERE order_id = 1
                """
            )

    with pytest.raises(quality.QualityCheckError, match="fact_matches_staging"):
        pipeline.check_quality()

    pipeline.build_warehouse()
    pipeline.check_quality()


def test_a_change_outside_the_lookback_is_caught_and_repaired(
    loaded_platform, monkeypatch
):
    with closing(connect_mysql(Settings())) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                UPDATE orders
                SET amount = amount + 100,
                    updated_at = UTC_TIMESTAMP(6) - INTERVAL 2 HOUR
                WHERE order_id = 2
                """
            )
        connection.commit()

    pipeline.load_orders()
    pipeline.build_warehouse()
    with pytest.raises(quality.QualityCheckError, match="warehouse_matches_source"):
        pipeline.check_quality()

    monkeypatch.setenv("CARTPULSE_WATERMARK_LOOKBACK_SECONDS", "86400")
    for step in pipeline.STEPS:
        step()

    assert warehouse_value("SELECT amount FROM dw.fact_sales WHERE order_id = 2") == (
        source_value("SELECT amount FROM orders WHERE order_id = 2")
    )
