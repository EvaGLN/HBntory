#!/usr/bin/python3
"""Manage database connections and external product tools during a request"""

# 'g' (global) is a temporary storage box for a single user request.
# Data can be stored inside and be accessible anywhere during the request.
# 'g' is cleared and deleted once the server sends the response back.
from flask import current_app, g


def get_database():
    """Open a new database session or reuse the existing one for the current request."""
    if "database" not in g:
        # 'current_app.extensions' is a built-in dictionary on the Flask app to store shared tools.
        # We grab the 'session_factory' tool and call it '()' to create a new database session.
        g.database = current_app.extensions["session_factory"]()
    return g.database


def get_products():
    """Fetch the shared API client used to interact with product data."""
    return current_app.extensions["product_client"]


def close_database(exc=None):
    """Shut down the active database session at the end of the request"""
    # 'pop' removes and returns 'database' from 'g'. If it was never opened, return None.
    database = g.pop("database", None)
    if database is not None:
        database.close()
