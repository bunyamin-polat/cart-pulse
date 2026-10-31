from datetime import date, datetime
from decimal import Decimal

import pytest

from cartpulse import quality
from tests.fakes import FakeConnection, FakeCursor

WATERMARK = datetime(2021, 12, 1)
DAY = date(2021, 11, 30)
GROUP = (DAY, "Spain", "Books", 2, Decimal("150.00"), 0)


def run_checks(violations, source_rows=(GROUP,), warehouse_rows=(GROUP,)):
    target = FakeCursor(
        fetchone_results=[*[(count,) for count in violations], (WATERMARK,)],
        fetchall_results=[list(warehouse_rows)],
    )
    source = FakeCursor(fetchall_results=[list(source_rows)])
    return FakeConnection(source), FakeConnection(target)


def no_violations():
    return [0] * len(quality.WAREHOUSE_CHECKS)


def test_clean_data_passes():
    source, target = run_checks(no_violations())

    assert quality.find_failures(source, target) == {}


def test_a_failed_check_is_reported_with_its_violations():
    violations = no_violations()
    names = list(quality.WAREHOUSE_CHECKS)
    violations[names.index("amounts_are_positive")] = 3
    source, target = run_checks(violations)

    assert quality.find_failures(source, target) == {"amounts_are_positive": 3}


def test_missing_rows_fail_the_reconciliation():
    short = (DAY, "Spain", "Books", 1, Decimal("150.00"), 0)
    source, target = run_checks(no_violations(), warehouse_rows=[short])

    assert quality.find_failures(source, target) == {"warehouse_matches_source": 1}


def test_a_changed_amount_fails_even_when_the_row_count_matches():
    changed = (DAY, "Spain", "Books", 2, Decimal("175.00"), 0)
    source, target = run_checks(no_violations(), warehouse_rows=[changed])

    assert quality.find_failures(source, target) == {"warehouse_matches_source": 1}


def test_a_wrong_dimension_fails_even_when_the_totals_match():
    moved = (DAY, "Italy", "Books", 2, Decimal("150.00"), 0)
    source, target = run_checks(no_violations(), warehouse_rows=[moved])

    assert quality.find_failures(source, target) == {"warehouse_matches_source": 2}


def test_a_run_without_a_watermark_fails():
    target = FakeCursor(
        fetchone_results=[*[(count,) for count in no_violations()], None]
    )

    failures = quality.find_failures(FakeConnection(), FakeConnection(target))

    assert failures == {"orders_were_loaded": 1}


def test_facts_are_compared_with_their_order_dimensions():
    query = quality.WAREHOUSE_CHECKS["fact_matches_staging"]

    assert "o.order_date <> d.full_date" in query
    assert "o.country <> c.country" in query
    assert "o.category <> k.category" in query


def test_failures_stop_the_pipeline():
    source, target = run_checks([1] * len(quality.WAREHOUSE_CHECKS))

    with pytest.raises(quality.QualityCheckError):
        quality.assert_quality(source, target)
