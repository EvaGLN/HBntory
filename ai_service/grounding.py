"""
Module containing the instruction for the AI and a callback called after each
tool.
"""

import json

UNAVAILABLE_MESSAGE = "I don't have enough information to answer that."
PRODUCT_FIELDS = ("sku", "name", "description", "unit_price", "currency")
SYSTEM_PROMPT = """You are the HBntory assistant for customers.
Use ONLY data returned by your tools. Never invent product names, details,
prices, quantities or branches.
Tool results have a "status" or an "error" field: if it is not ok, or no data
came back, answer exactly: I don't have enough information to answer that.
Questions you can answer: product details, where a product is in stock, what a
branch has in stock, which branch(es) to visit for a shopping list.
For anything else, say you can only help with products and stock.
Never mention tools, databases or internal identifiers other than product id.
Answer briefly in the language of the question."""


def trim_product(product):
    return {k: product[k] for k in PRODUCT_FIELDS if k in product}


def trim_tool_response(tool, args, tool_context, tool_response):
    if tool.name != "get_product":
        return None

    try:
        payload = json.loads(tool_response["content"][0]["text"])
        payload["product"] = trim_product(payload["product"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None

    return {"content": [{"type": "text", "text": json.dumps(payload)}],
            "isError": False}
