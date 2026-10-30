"""Unit tests for the incremental ETL, using fake database connections."""

import automation


class FakeCursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def close(self):
        pass

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, cursor=None):
        self.fake_cursor = cursor or FakeCursor()
        self.cursor_calls = 0
        self.transactions = 0

    def __enter__(self):
        self.transactions += 1
        return self

    def __exit__(self, *exc_info):
        return False

    def cursor(self):
        self.cursor_calls += 1
        return self.fake_cursor


def test_get_last_rowid_returns_the_highest_rowid():
    connection = FakeConnection(FakeCursor(row=(12289,)))

    assert automation.get_last_rowid(connection) == 12289


def test_get_last_rowid_treats_an_empty_table_as_zero():
    cursor = FakeCursor(row=(0,))

    automation.get_last_rowid(FakeConnection(cursor))

    assert "COALESCE(MAX(rowid), 0)" in cursor.executed[0][0]


def test_get_latest_records_passes_rowid_as_a_parameter():
    records = [(12290, 6715, 80213, 1)]
    cursor = FakeCursor(rows=records)

    result = automation.get_latest_records(FakeConnection(cursor), 12289)

    query, params = cursor.executed[0]
    assert result == records
    assert "rowid > %s" in query
    assert params == (12289,)


def test_insert_records_writes_in_one_transaction(monkeypatch):
    calls = []
    monkeypatch.setattr(
        automation,
        "execute_values",
        lambda cursor, query, records: calls.append((query, records)),
    )
    records = [(12290, 6715, 80213, 1), (12291, 6716, 80214, 2)]
    connection = FakeConnection()

    automation.insert_records(connection, records)

    assert connection.transactions == 1
    assert len(calls) == 1
    assert "price" not in calls[0][0]
    assert calls[0][1] == records


def test_insert_records_skips_an_empty_list():
    connection = FakeConnection()

    automation.insert_records(connection, [])

    assert connection.cursor_calls == 0
    assert connection.transactions == 0
