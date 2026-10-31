"""Small stand-ins for database connections, so unit tests need no database."""


class FakeCursor:
    def __init__(
        self, fetchone_results=(), fetchall_results=(), batches=(), rowcount=0
    ):
        self.fetchone_results = list(fetchone_results)
        self.fetchall_results = list(fetchall_results)
        self.batches = list(batches)
        self.rowcount = rowcount
        self.executed = []
        self.copied = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def close(self):
        pass

    def execute(self, query, params=None):
        self.executed.append((" ".join(query.split()), params))

    def fetchone(self):
        return self.fetchone_results.pop(0)

    def fetchall(self):
        return self.fetchall_results.pop(0)

    def fetchmany(self, size):
        return self.batches.pop(0) if self.batches else []

    def copy_expert(self, statement, buffer):
        self.copied.append((statement, buffer.read()))


class FakeConnection:
    def __init__(self, cursor=None):
        self.fake_cursor = cursor or FakeCursor()
        self.transactions = 0

    def __enter__(self):
        self.transactions += 1
        return self

    def __exit__(self, *exc_info):
        return False

    def cursor(self):
        return self.fake_cursor
