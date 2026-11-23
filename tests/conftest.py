#!/usr/bin/python3
"""Shared pytest fixtures: fake Products API and app factory."""

from flask import Flask, jsonify
from werkzeug.serving import make_server

import os
import sys
import threading
import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
for folder in ("backoffice", "ai_service", "product_mcp_server"):
    sys.path.insert(0, os.path.join(ROOT, folder))

PRODUCTS = {
    "HB-LAP-1001": {"sku": "HB-LAP-1001", "name": "Laptop",
                    "unit_price": 799.0},
    "HB-MON-2101": {"sku": "HB-MON-2101", "name": "Monitor",
                    "unit_price": 199.0},
    "HB-KBD-4101": {"sku": "HB-KBD-4101", "name": "Keyboard",
                    "unit_price": 49.0},
}


def fake_api():
    """Tiny Flask app that mimics the real Products API."""
    api = Flask("fake_products")

    @api.get("/api/v1/products")
    def list_all():
        return jsonify(results=list(PRODUCTS.values()))

    @api.get("/api/v1/products/<sku>")
    def get_one(sku):
        if sku not in PRODUCTS:
            return jsonify(error="not found"), 404
        return jsonify(PRODUCTS[sku])
    return api


@pytest.fixture(scope="session")
def product_api_url():
    """Start the fake API on a free port, once for the whole test run."""
    server = make_server("127.0.0.1", 0, fake_api())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/api/v1"
    server.shutdown()


@pytest.fixture
def make_app(tmp_path, product_api_url):
    """Return a function that builds an app on a fresh SQLite file."""
    from app import create_app
    from products_client import ProductClient

    def _make():
        return create_app(f"sqlite:///{tmp_path}/test.db",
                          ProductClient(product_api_url),
                          "test-secret-key-0123456789")
    return _make
