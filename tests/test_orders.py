from datetime import date, datetime, timedelta

from cartpulse import orders
from tests.fakes import FakeConnection, FakeCursor

FIRST_CHANGE = datetime(2021, 12, 1, 8, 0)
LATEST_CHANGE = datetime(2021, 12, 1, 9, 30)


def order(order_id, updated_at):
    return (order_id, date(2021, 12, 1), "Spain", "Books", 100, "completed", updated_at)


def run_sync(watermark, batches, rowcount=0):
    source = FakeConnection(FakeCursor(batches=batches))
    target = FakeConnection(
        FakeCursor(fetchone_results=[(watermark,)], rowcount=rowcount)
    )
    result = orders.sync(source, target, lookback_seconds=300)
    return result, source.fake_cursor, target


def test_first_run_starts_from_the_initial_watermark():
    cursor = FakeCursor(fetchone_results=[None])

    assert orders.get_watermark(cursor) == orders.INITIAL_WATERMARK


def test_extract_goes_back_by_the_lookback_window():
    watermark = datetime(2021, 12, 1, 12, 0)

    _, source_cursor, _ = run_sync(watermark, batches=[])

    assert source_cursor.executed[0][1] == (watermark - timedelta(seconds=300),)


def test_watermark_moves_to_the_latest_change_seen():
    batches = [[order(1, FIRST_CHANGE), order(2, LATEST_CHANGE)]]

    result, _, target = run_sync(FIRST_CHANGE, batches, rowcount=2)

    saved = [params for _, params in target.fake_cursor.executed if params]
    assert (orders.SOURCE, LATEST_CHANGE) in saved
    assert result.high_water_mark == LATEST_CHANGE
    assert result.rows_extracted == 2
    assert result.rows_changed == 2


def test_watermark_never_moves_backwards():
    late_commit = FIRST_CHANGE - timedelta(minutes=1)

    result, _, _ = run_sync(FIRST_CHANGE, [[order(1, late_commit)]])

    assert result.high_water_mark == FIRST_CHANGE


def test_rows_and_watermark_share_one_transaction():
    _, _, target = run_sync(FIRST_CHANGE, [[order(1, LATEST_CHANGE)]])

    assert target.transactions == 1


def test_all_batches_reach_the_warehouse():
    batches = [[order(1, FIRST_CHANGE)], [order(2, LATEST_CHANGE)]]

    result, _, target = run_sync(FIRST_CHANGE, batches)

    assert len(target.fake_cursor.copied) == 2
    assert result.rows_extracted == 2


def test_rerun_of_unchanged_rows_counts_nothing_as_changed():
    assert "IS DISTINCT FROM EXCLUDED.updated_at" in orders.UPSERT_QUERY
