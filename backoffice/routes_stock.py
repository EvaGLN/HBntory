#!/usr/bin/python3
"""Manage branch inventory endpoints for viewing and updating stock."""

from flask import Blueprint, g, jsonify, request
from authentication import common_required
from dependencies import get_database, get_products
from products_client import ProductApiError
from stock_service import (StockError, add_stock, get_quantity,
                           list_branch_stock, remove_stock)

bp = Blueprint("stock", __name__)

STATUS = {"invalid_quantity": 400, "branch_not_found": 404,
          "product_not_found": 404, "insufficient_stock": 409}


def own_branch_only(branch_id):
    """Ensure the logged-in common user only accesses its own branch."""
    if branch_id != g.user.branch_id:
        return jsonify(error="forbidden: another branch"), 403
    return None


@bp.get("/branches/<int:branch_id>/stock")
@common_required
def list_stock(branch_id):
    """Return all product quantities available in a specific branch."""
    denied = own_branch_only(branch_id)
    if denied:
        return denied
    return jsonify(branch_id=branch_id, products=list_branch_stock(
        get_database(), branch_id))


@bp.get("/branches/<int:branch_id>/stock/<product_id>")
@common_required
def one_quantity(branch_id, product_id):
    """Fetch the stock count for a specific product in a branch."""
    denied = own_branch_only(branch_id)
    if denied:
        return denied
    return jsonify(product_id=product_id, quantity=get_quantity(
        get_database(), branch_id, product_id))


def change_stock(branch_id, action):
    """Validate increase or decrease quantity request."""
    denied = own_branch_only(branch_id)
    if denied:
        return denied
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    product_id = data.get("product_id")
    if not isinstance(product_id, str) or not product_id:
        return jsonify(error="product_id is required"), 400
    try:
        if action == "add":
            total = add_stock(get_database(), branch_id,
                              product_id, data.get("quantity"), get_products())
        else:
            total = remove_stock(get_database(), branch_id,
                                 product_id, data.get("quantity"))
    except StockError as exc:
        return jsonify(error=str(exc), code=exc.code), STATUS[exc.code]
    except ProductApiError:
        return jsonify(error="product API unavailable"), 502
    return jsonify(product_id=product_id, quantity=total)


@bp.post("/branches/<int:branch_id>/stock/add")
@common_required
def add_route(branch_id):
    """Handle request to add stock in a specific branch."""
    return change_stock(branch_id, "add")


@bp.post("/branches/<int:branch_id>/stock/remove")
@common_required
def remove_route(branch_id):
    """Handle request to remove stock in a specific branch."""
    return change_stock(branch_id, "remove")
