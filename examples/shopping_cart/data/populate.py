"""Load generated MongoDB fixtures into the shopping cart example."""

import argparse
from decimal import DecimalException
import os
from pathlib import Path
from typing import Any

from bson import ObjectId, json_util
from bson.errors import BSONError
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError, PyMongoError


def read_fixture(path: Path) -> dict[ObjectId, dict[str, Any]]:
    """Read an Extended JSON array indexed by its explicit ObjectIds."""
    try:
        documents = json_util.loads(path.read_text(encoding="utf-8"))
    except (BSONError, DecimalException, OverflowError, TypeError, ValueError) as error:
        raise ValueError(f"{path}: invalid Extended JSON ({error}).") from error
    if not isinstance(documents, list):
        raise ValueError(f"{path}: expected an Extended JSON array of documents.")

    by_id = {}
    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict) or not isinstance(document.get("_id"), ObjectId):
            raise ValueError(f"{path}: document {index} requires an ObjectId _id.")
        document_id = document["_id"]
        if document_id in by_id:
            raise ValueError(f"{path}: duplicate _id {document_id}.")
        by_id[document_id] = document
    return by_id


def referenced_products(orders: dict[ObjectId, dict[str, Any]]) -> set[ObjectId]:
    """Validate the fields needed to resolve each order's dependencies."""
    references = set()
    for order_id, order in orders.items():
        customer = order.get("customer_id")
        if type(customer) is not str or not customer:
            raise ValueError(f"Order {order_id} requires a nonempty customer_id string.")
        items = order.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"Order {order_id} requires a nonempty items array.")
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict) or not isinstance(item.get("product_id"), ObjectId):
                raise ValueError(f"Order {order_id}, item {index}, requires an ObjectId product_id.")
            references.add(item["product_id"])
    return references


def find_documents(
    collection: Collection, ids: set[ObjectId],
) -> dict[ObjectId, dict[str, Any]]:
    """Read existing documents for the fixture and its product references."""
    return {document["_id"]: document for document in collection.find({"_id": {"$in": list(ids)}})}


def pending_inserts(
    name: str, fixture: dict[ObjectId, dict[str, Any]], existing: dict[ObjectId, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Skip identical records and reject ID collisions before inserting."""
    pending = []
    options = {"json_options": json_util.CANONICAL_JSON_OPTIONS, "sort_keys": True}
    for document_id, document in fixture.items():
        if document_id not in existing:
            pending.append(document)
        elif json_util.dumps(document, **options) != json_util.dumps(existing[document_id], **options):
            raise ValueError(f"{name}: _id {document_id} already exists with different data.")
    return pending


def insert_documents(
    collection: Collection, pending: list[dict[str, Any]], skipped: int,
) -> None:
    """Insert one collection's pending documents and report its result."""
    if pending:
        try:
            collection.insert_many(pending, ordered=True)
        except BulkWriteError as error:
            details = error.details
            failure = next(iter(details.get("writeErrors", [])), None)
            reason = (
                f"_id {pending[failure['index']]['_id']}, MongoDB error {failure['code']}"
                if failure else "bulk write failed"
            )
            raise ValueError(
                f"{collection.name}: {reason}. MongoDB reported "
                f"{details.get('nInserted', 0)} inserts in this batch. "
                "Earlier writes may persist. Retry with the same fixture IDs."
            ) from error
        except (BSONError, PyMongoError) as error:
            raise ValueError(
                f"{collection.name}: insert failed ({type(error).__name__}). "
                "Earlier writes may persist. Retry with the same fixture IDs."
            ) from error
    print(f"{collection.name}: inserted {len(pending)}, skipped {skipped}")


def populate(
    database: Database,
    orders: dict[ObjectId, dict[str, Any]],
    products: dict[ObjectId, dict[str, Any]],
) -> None:
    """Check references and conflicts, then insert products before orders."""
    references = referenced_products(orders)
    missing_collections = {"products", "orders"} - set(database.list_collection_names())
    if missing_collections:
        missing = ", ".join(sorted(missing_collections))
        raise ValueError(f"Missing collections: {missing}. Run data/create_collections.py first.")

    existing_products = find_documents(database.products, references | products.keys())
    unresolved = references - existing_products.keys() - products.keys()
    if unresolved:
        raise ValueError(f"Missing product IDs: {', '.join(map(str, sorted(unresolved)))}.")

    new_products = pending_inserts("products", products, existing_products)
    existing_orders = find_documents(database.orders, set(orders))
    new_orders = pending_inserts("orders", orders, existing_orders)
    insert_documents(database.products, new_products, len(products) - len(new_products))
    insert_documents(database.orders, new_orders, len(orders) - len(new_orders))


def main() -> None:
    """Parse fixture paths and connect to the initialized shopping cart database."""
    parser = argparse.ArgumentParser(
        prog="uv run --locked data/populate.py",
        description="Load shopping cart orders and products from Extended JSON arrays.",
        epilog=(
            "Run data/create_collections.py first. Each document needs an explicit, unique "
            "ObjectId _id. Every order product ID must exist or be provided by --products. "
            "Set MONGODB_URI to override mongodb://127.0.0.1:27017. "
            "If a write fails, earlier writes may persist. Retry with the same fixture IDs "
            "to skip identical documents. Conflicting documents are rejected."
        ),
    )
    parser.add_argument("--orders", type=Path, required=True, help="Order fixture path")
    parser.add_argument("--products", type=Path, help="Product fixture path")
    args = parser.parse_args()

    try:
        orders = read_fixture(args.orders)
        products = read_fixture(args.products) if args.products else {}
        uri = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017")
        with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
            populate(client["shopping_cart"], orders, products)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")
    except PyMongoError as error:
        parser.exit(1, f"{parser.prog}: MongoDB preflight failed ({type(error).__name__}).\n")


if __name__ == "__main__":
    main()
