"""
The business layer for the stock management. Allow to add or remove from stocks
and apply validation rules to ensure the operation never break the data base.
It uses the Branch and Stock models from model.py. Contrary to seed.py, each
function do it's own commit.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models import Branch, Stock


class StockError(ValueError):
    """
    Custom execption which inherit from ValueError.
    It give to information:
        - A message that can be read by a human.
        - An error code that can be used by an API.
    """

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def check_quantity(quantity):
    """
    Check that the quantity is strictly positive and of valid type.
    We use 'isinstance(quantity, bool)' because True could be interpreted be
    Python as a 1.
    """

    if isinstance(quantity, bool) or not isinstance(quantity, int) or \
       quantity <= 0:
        raise StockError("invalid_quantity", "quantity must be a positive " +
                         "integer")


def require_branch(session, branch_id):
    """
    Check if the given branch exists.
    """

    if session.get(Branch, branch_id) is None:
        raise StockError("branch_not_found", "unknown branch")


def add_stock(session, branch_id, product_id, quantity, products):
    """
    Take products, an external object which can tell if a product exists.
    As models.py doesn't have a products table, the existence of a product is
    check elsewhere.
    Also allow the common user to increment the stock of the given product.

    Two limitation to know:
        - If two request are made at the same time, the seconde one will fail with
          a IntegrityError, which is not handle here.
        - No rollback if the commit fail.
    """

    check_quantity(quantity)
    require_branch(session, branch_id)

    if not products.exists(product_id):
        raise StockError("product_not_found", "unknown product")

    row = session.get(Stock, (branch_id, product_id), with_for_update=True)

    if row is None:
        row = Stock(branch_id=branch_id, product_id=product_id, quantity=0)
        session.add(row)

    row.quantity += quantity
    session.commit()

    return row.quantity


def remove_stock(session, branch_id, product_id, quantity):
    """
    Allow the common user to increment the stock of the given product.
    Contrary to 'add_stock' we don't need 'products', removing a product that
    doesn't exist is the same as running out of stock.
    """

    check_quantity(quantity)
    require_branch(session, branch_id)

    row = session.get(Stock, (branch_id, product_id), with_for_update=True)
    if row is None or row.quantity < quantity:
        raise StockError("insufficient_stock", "not enough stock")

    row.quantity -= quantity

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise StockError("insufficient_stock", "not enough stock") from exc

    return row.quantity


def get_quantity(session, branch_id, product_id):
    """
    Get the stock for a given product, if the product doesn't exists, the stock
    is equal to 0.
    """
    row = session.get(Stock, (branch_id, product_id))

    return row.quantity if row else 0


def list_branch_stock(session, branch_id):
    """
    Make a request to list the stock of all product of a given branch.
    """
    rows = session.scalars(select(Stock).where(Stock.branch_id == branch_id,
                           Stock.quantity > 0).order_by(Stock.product_id))

    return [{"product_id": r.product_id, "quantity": r.quantity} for r in rows]
