"""Full refresh of the product catalog from MongoDB into the warehouse."""

from cartpulse.warehouse import copy_rows, record_load

SOURCE = "catalog"
COLUMNS = ("product_id", "product_type", "model", "screen_size", "ram", "hard_disk")


def to_row(document):
    """Flatten a document. Attributes that a product type lacks become NULL."""
    return (
        str(document["_id"]),
        document["type"],
        document["model"],
        document.get("screen size"),
        document.get("ram"),
        document.get("hard disk"),
    )


def sync(collection, target):
    """Replace the warehouse copy in one transaction, so readers never see it empty."""
    rows = [to_row(document) for document in collection.find()]

    with target, target.cursor() as cursor:
        cursor.execute("TRUNCATE staging.catalog_products")
        copy_rows(cursor, "staging.catalog_products", COLUMNS, rows)
        record_load(cursor, SOURCE, len(rows), len(rows))

    return len(rows)
