#!/usr/bin/python3
"""Initialize and run the main HBntory Flask web application."""

import os

from flask import Flask
from sqlalchemy.orm import sessionmaker
from routes_admin import bp as admin_bp
from routes_authentication import bp as authentication_bp
from routes_products import bp as products_bp
from routes_stock import bp as stock_bp
from dependencies import close_database
from models import create_tables, make_engine
from products_client import ProductClient


def create_app(database_url, product_client, secret_key):
    """Build and configure the Flask app with its database, clients and routes."""
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["SECRET_KEY"] = secret_key
    engine = make_engine(database_url)
    create_tables(engine)
    app.extensions["session_factory"] = sessionmaker(engine)
    app.extensions["product_client"] = product_client
    app.teardown_appcontext(close_database)
    for blueprint in (authentication_bp, stock_bp, admin_bp, products_bp):
        app.register_blueprint(blueprint)
    return app

if __name__ == "__main__":
    application = create_app(
        os.environ.get("DATABASE_URL", "sqlite:///hbntory.db"),
        ProductClient(os.environ.get("PRODUCT_API_URL",
                                     "http://localhost:8000")),
        os.environ["SECRET_KEY"],
    )
    application.run(port=5000)
