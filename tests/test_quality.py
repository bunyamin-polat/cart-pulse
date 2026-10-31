from datetime import date, datetime
from decimal import Decimal

import pytest

from cartpulse import quality
from tests.fakes import FakeConnection, FakeCursor

WATERMARK = datetime(2021, 12, 1)
DAY = date(2021, 11, 30)
ORDER = (1, DAY, "Spain", "Books", Decimal("150.00"), "completed")
OTHER = (2, DAY, "Spain", "Books", Decimal("50.00"), "completed")


class FakeCatalog:
    def __init__(self, documents=438):
        self.documents = documents

    def count_documents(self, query):
        return self.documents


def run_checks(
    violations,
    source_rows=(ORDER,),
    warehouse_rows=(ORDER,),
    catalog_rows=438,
):
    target = FakeCursor(
        fetchone_results=[
            *[(count,) for count in violations],
            (catalog_rows,),
            (WATERMARK,),
        ],
        fetchall_results=[list(warehouse_rows)],
    )
    source = FakeCursor(fetchall_results=[list(source_rows)])
    return FakeConnection(source), FakeConnection(target)


def no_violations():
    return [0] * len(quality.WAREHOUSE_CHECKS)


def test_clean_data_passes():
    source, target = run_checks(no_violations())

    assert quality.find_failures(source, target, FakeCatalog()) == {}


def test_a_failed_check_is_reported_with_its_violations():
    violations = no_violations()
    names = list(quality.WAREHOUSE_CHECKS)
    violations[names.index("amounts_are_positive")] = 3
    source, target = run_checks(violations)

    failures = quality.find_failures(source, target, FakeCatalog())

    assert failures == {"amounts_are_positive": 3}


def test_a_missing_order_fails_the_reconciliation():
    source, target = run_checks(no_violations(), warehouse_rows=[])

    failures = quality.find_failures(source, target, FakeCatalog())

    assert failures == {"warehouse_matches_source": 1}


def test_a_changed_amount_fails_the_reconciliation():
    changed = (1, DAY, "Spain", "Books", Decimal("175.00"), "completed")
    source, target = run_checks(no_violations(), warehouse_rows=[changed])

    failures = quality.find_failures(source, target, FakeCatalog())

    assert failures == {"warehouse_matches_source": 1}


def test_a_wrong_dimension_fails_the_reconciliation():
    moved = (1, DAY, "Italy", "Books", Decimal("150.00"), "completed")
    source, target = run_checks(no_violations(), warehouse_rows=[moved])

    failures = quality.find_failures(source, target, FakeCatalog())

    assert failures == {"warehouse_matches_source": 1}


def test_changes_that_cancel_out_are_still_caught():
    higher = (1, DAY, "Spain", "Books", Decimal("160.00"), "completed")
    lower = (2, DAY, "Spain", "Books", Decimal("40.00"), "completed")

    differences = quality.count_differences([ORDER, OTHER], [higher, lower])

    assert differences == 2


def test_a_missing_product_fails_the_catalog_check():
    source, target = run_checks(no_violations(), catalog_rows=437)

    failures = quality.find_failures(source, target, FakeCatalog())

    assert failures == {"catalog_matches_source": 1}


def test_a_run_without_a_watermark_fails():
    target = FakeCursor(
        fetchone_results=[*[(count,) for count in no_violations()], (438,), None]
    )

    failures = quality.find_failures(
        FakeConnection(), FakeConnection(target), FakeCatalog()
    )

    assert failures == {"orders_were_loaded": 1}


def test_facts_are_compared_with_their_order_dimensions():
    query = quality.WAREHOUSE_CHECKS["fact_matches_staging"]

    assert "o.order_date <> d.full_date" in query
    assert "o.country <> c.country" in query
    assert "o.category <> k.category" in query


def test_failures_stop_the_pipeline():
    source, target = run_checks([1] * len(quality.WAREHOUSE_CHECKS))

    with pytest.raises(quality.QualityCheckError):
        quality.assert_quality(source, target, FakeCatalog())
