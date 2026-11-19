"""
Module containing all the tools needed by the AI to work with stocks.
"""

from sqlalchemy.orm import sessionmaker
from stock_queries import branch_stock, plan_shopping_list, where_is_product

SessionLocal = None


def configure(engine):
    global SessionLocal
    SessionLocal = sessionmaker(engine)


def find_product_stock(product_id: str) -> dict:
    """Return which branches have stock of a product, with quantities"""

    with SessionLocal() as session:
        rows = where_is_product(session, product_id)

    return {"status": "ok", "branches": rows} if rows else {
            "status": "no stock", "branches": []
           }


def find_branch_stock(branch_name: str) -> dict:
    """Return the products currently in stock in on branch"""

    with SessionLocal() as session:
        result = branch_stock(session, branch_name)

    return {"status": "unknown branch"} if result is None else {
            "status": "ok", **result
           }


def find_shopping_plan(wanted: dict[str, int]) -> dict:
    """
    Given {product_id: quantity}, say which branch(es) can satisfy the list.
    """

    with SessionLocal() as session:
        return {"status": "ok", **plan_shopping_list(session, wanted)}


STOCK_TOOLS = [find_product_stock, find_branch_stock, find_shopping_plan]
