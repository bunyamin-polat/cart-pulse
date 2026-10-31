"""Data quality checks that stand between the warehouse and the marts."""

from contextlib import closing

# Each query counts violations, so 0 means the check passed.
WAREHOUSE_CHECKS = {
    "staging_has_orders": """
        SELECT CASE WHEN EXISTS (SELECT 1 FROM staging.orders) THEN 0 ELSE 1 END
    """,
    "catalog_has_products": """
        SELECT CASE WHEN EXISTS (SELECT 1 FROM staging.catalog_products)
            THEN 0 ELSE 1 END
    """,
    "web_requests_loaded": """
        SELECT CASE WHEN EXISTS (SELECT 1 FROM staging.web_requests) THEN 0 ELSE 1 END
    """,
    "web_traffic_matches_log": """
        SELECT COALESCE(
            (
                SELECT CASE
                    WHEN rows_extracted = rows_changed + rows_excluded + rows_rejected
                        AND rows_changed = (SELECT COUNT(*) FROM staging.web_requests)
                    THEN 0 ELSE 1
                END
                FROM etl.load_audit
                WHERE source = 'web_traffic'
                ORDER BY load_id DESC
                LIMIT 1
            ),
            1
        )
    """,
    # The joins prove each fact still points at its order's date, country and category.
    "fact_matches_staging": """
        SELECT COUNT(*)
        FROM staging.orders o
        FULL JOIN dw.fact_sales f USING (order_id)
        LEFT JOIN dw.dim_date d ON d.date_key = f.date_key
        LEFT JOIN dw.dim_country c ON c.country_key = f.country_key
        LEFT JOIN dw.dim_category k ON k.category_key = f.category_key
        WHERE o.order_id IS NULL
            OR f.order_id IS NULL
            OR o.amount <> f.amount
            OR o.status <> f.status
            OR o.order_date <> d.full_date
            OR o.country <> c.country
            OR o.category <> k.category
    """,
    "amounts_are_positive": "SELECT COUNT(*) FROM dw.fact_sales WHERE amount <= 0",
    "status_is_known": """
        SELECT COUNT(*) FROM dw.fact_sales
        WHERE status NOT IN ('completed', 'cancelled')
    """,
    "orders_are_not_in_the_future": """
        SELECT COUNT(*) FROM staging.orders WHERE order_date > CURRENT_DATE
    """,
    "dates_match_the_calendar": """
        SELECT COUNT(*) FROM dw.dim_date
        WHERE year <> extract(year FROM full_date)
            OR quarter <> extract(quarter FROM full_date)
            OR month <> extract(month FROM full_date)
            OR day <> extract(day FROM full_date)
            OR weekday <> extract(isodow FROM full_date)
    """,
}

WATERMARK_QUERY = "SELECT high_water_mark FROM etl.watermarks WHERE source = 'orders'"

CATALOG_COUNT_QUERY = "SELECT COUNT(*) FROM staging.catalog_products"

# Every order is compared on its own, because totals can hide changes that cancel out.
SOURCE_ORDERS_QUERY = """
    SELECT order_id, order_date, country, category, amount, status
    FROM orders
    WHERE updated_at <= %s
"""

WAREHOUSE_ORDERS_QUERY = """
    SELECT f.order_id, d.full_date, c.country, k.category, f.amount, f.status
    FROM dw.fact_sales f
    JOIN staging.orders o USING (order_id)
    JOIN dw.dim_date d ON d.date_key = f.date_key
    JOIN dw.dim_country c ON c.country_key = f.country_key
    JOIN dw.dim_category k ON k.category_key = f.category_key
    WHERE o.updated_at <= %s
"""


class QualityCheckError(RuntimeError):
    """At least one check failed, so the marts must not be refreshed."""


def count_differences(source_rows, warehouse_rows):
    """Return how many orders differ between the source and the warehouse."""
    source = {row[0]: tuple(row[1:]) for row in source_rows}
    warehouse = {row[0]: tuple(row[1:]) for row in warehouse_rows}
    return sum(source.get(key) != warehouse.get(key) for key in source | warehouse)


def find_failures(source, target, catalog):
    """Return a dictionary of failed checks and how many violations each one found."""
    failures = {}

    with target, target.cursor() as cursor:
        for name, query in WAREHOUSE_CHECKS.items():
            cursor.execute(query)
            violations = cursor.fetchone()[0]
            if violations:
                failures[name] = violations

        cursor.execute(CATALOG_COUNT_QUERY)
        catalog_rows = cursor.fetchone()[0]

        cursor.execute(WATERMARK_QUERY)
        row = cursor.fetchone()
        if row is None:
            failures["orders_were_loaded"] = 1
            return failures

        # Comparing up to the watermark ignores orders that arrived after this load.
        watermark = row[0]
        cursor.execute(WAREHOUSE_ORDERS_QUERY, (watermark,))
        warehouse_rows = cursor.fetchall()

    with closing(source.cursor()) as cursor:
        cursor.execute(SOURCE_ORDERS_QUERY, (watermark,))
        source_rows = cursor.fetchall()

    differences = count_differences(source_rows, warehouse_rows)
    if differences:
        failures["warehouse_matches_source"] = differences

    missing_products = abs(catalog.count_documents({}) - catalog_rows)
    if missing_products:
        failures["catalog_matches_source"] = missing_products

    return failures


def assert_quality(source, target, catalog):
    failures = find_failures(source, target, catalog)
    if failures:
        raise QualityCheckError(f"Failed checks: {failures}")
