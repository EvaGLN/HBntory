#!/usr/bin/python3
"""Expose endpoints to browse catalog products for signed-in users."""

from flask import Blueprint, jsonify
from authentication import login_required
from dependencies import get_products
from products_client import ProductApiError, ProductNotFound

bp = Blueprint("products", __name__)


@bp.get("/products")
@login_required
def product_list():
    """Return the full list of available products as JSON."""
    try:
        return jsonify(get_products().list_products())
    except ProductApiError:
        return jsonify(error="product API unavailable"), 502


@bp.get("/products/<product_id>")
@login_required
def one_product(product_id):
    """Fetch and return details for a single product by its ID."""
    try:
        return jsonify(get_products().get_product(product_id))
    except ProductNotFound:
        return jsonify(error="unknown product"), 404
    except ProductApiError:
        return jsonify(error="product API unavailable"), 502
