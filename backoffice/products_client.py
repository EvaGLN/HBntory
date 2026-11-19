#!/usr/bin/python3
"""Communicate with the catalog API service over HTTP.
SKU: Stock Keeping Unit"""

# Import quote to encode special characters (spaces, slashes...) so they are safe for URLs
from urllib.parse import quote

import requests


class ProductApiError(Exception):
    """Raised when the catalog API service fails or is unreachable."""
    pass


class ProductNotFound(Exception):
    """Raised when a requested product ID does not exist in the catalog API."""
    pass


class ProductClient:
    """HTTP client used to query products from the catalog API."""
    def __init__(self, base_url):
        """Store the server root URL without an ending slash to prevent breaking complementary URL paths"""
        self.base_url = base_url.rstrip("/")

    def list_products(self):
        """Fetch up to 100 products from the catalog API."""
        try:
            resp = requests.get(f"{self.base_url}/products",
                                params={"limit": 100}, timeout=5)
        except requests.RequestException as exc:
            raise ProductApiError("product API unreachable") from exc
        if resp.status_code != 200:
            raise ProductApiError(f"product API returned {resp.status_code}")
        return resp.json()["results"]

    def get_product(self, product_id):
        """Retrieve full details of a product by its ID."""
        try:
            # safe='' forces quote() to encode slashes, so an ID like "A/123" won't break the URL path
            url = f"{self.base_url}/products/{quote(product_id, safe='')}"
            resp = requests.get(url, timeout=5)
        except requests.RequestException as exc:
            raise ProductApiError("product API unreachable") from exc
        if resp.status_code == 404:
            raise ProductNotFound(product_id)
        if resp.status_code != 200:
            raise ProductApiError(f"product API returned {resp.status_code}")
        return resp.json()

    def exists(self, product_id):
        """Return True if a product ID is valid and matches its SKU."""
        try:
            product = self.get_product(product_id)
        except ProductNotFound:
            return False
        # SKU is a unique code used to identify a specific product in a store's inventory
        return product["sku"] == product_id
