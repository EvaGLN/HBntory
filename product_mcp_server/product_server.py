"""
This module create a MCP server, which use two tools in read-only:
    - list_products
    - get_product
An AI agent can use those tool to answer client questions.
"""

import os
import sys
import logging

from typing import Annotated
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from products_client import ProductClient, ProductApiError, ProductNotFound

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("product-mcp")

mcp = FastMCP("product-server")

client = ProductClient(os.environ.get("PRODUCT_API_URL",
                       "http://localhost:8000"))

DESCRIPTION = "Product identifier as returned by list_products."


@mcp.tool()
def list_products() -> dict:
    """List all available products (read-only)."""

    try:
        return {"products": client.list_products()}
    except ProductApiError as exc:
        log.error(f"list_products failed: {exc}")
        raise ValueError("The product service is currently invavailable") from\
            exc


@mcp.tool()
def get_product(product_id: Annotated[str, Field(description=DESCRIPTION)]) \
                -> dict:
    """Get the details of one product from its identifier."""

    try:
        return {"product": client.get_product(product_id)}
    except ProductNotFound as exc:
        raise ValueError(f"No product with id '{product_id}'.") from exc
    except ProductApiError as exc:
        log.error(f"get_product failed: {exc}")
        raise ValueError("The product service is currently invavailable") from\
            exc


if __name__ == "__main__":
    mcp.run()
