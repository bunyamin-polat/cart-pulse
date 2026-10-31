from cartpulse import catalog
from tests.fakes import FakeConnection


def test_attributes_a_product_lacks_become_null():
    document = {"_id": 1, "type": "smart phone", "model": "c3", "screen size": 6.5}

    assert catalog.to_row(document) == ("1", "smart phone", "c3", 6.5, None, None)


def test_refresh_replaces_the_table_in_one_transaction():
    class Collection:
        def find(self):
            return [{"_id": 1, "type": "laptop", "model": "x", "ram": "8GB"}]

    target = FakeConnection()

    assert catalog.sync(Collection(), target) == 1
    assert target.transactions == 1
    assert target.fake_cursor.executed[0][0] == "TRUNCATE staging.catalog_products"
