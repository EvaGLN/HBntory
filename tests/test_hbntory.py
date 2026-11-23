#!/usr/bin/python3
"""Integration tests for HBntory authentication, stock, user management and products."""

import pytest

from authentication import verify_password
from models import Stock, User
from seed import seed


@pytest.fixture
def app(make_app):
    """Create a test Flask app seeded with initial database data."""
    application = make_app()
    db = application.extensions["session_factory"]()
    seed(db, "adminpass1")
    db.commit()
    db.close()
    return application


@pytest.fixture
def login_as(app):
    """Provide a helper function to create and log in as a specific user."""
    def _login_as(username, branch_id=None):
        admin = app.test_client()
        admin.post("/login", json={"username": "admin", "password": "adminpass1"})
        if username != "admin":
            admin.post("/admin/users", json={"username": username, "password": "password1", "branch_id": branch_id})
        c = app.test_client()
        password = "adminpass1" if username == "admin" else "password1"
        assert c.post("/login", json={"username": username, "password": password}).status_code == 200
        return c
    return _login_as


def test_add_and_remove_valid(login_as):
    """Verify that adding and removing valid stock quantities updates the total correctly."""
    alice = login_as("alice", 1)
    assert alice.post("/branches/1/stock/add", json={"product_id": "HB-LAP-1001", "quantity": 5}).get_json()["quantity"] == 15
    assert alice.post("/branches/1/stock/remove", json={"product_id": "HB-LAP-1001", "quantity": 4}).get_json()["quantity"] == 11


def test_cannot_remove_more_than_available(login_as):
    """Ensure removing more items than available in stock fails with a 409 error."""
    alice = login_as("alice", 1)
    assert alice.post("/branches/1/stock/remove", json={"product_id": "HB-MON-2101", "quantity": 99}).status_code == 409
    assert alice.get("/branches/1/stock/HB-MON-2101").get_json()["quantity"] == 4


@pytest.mark.parametrize("bad", [0, -3, 1.5, "2", True, None])
def test_invalid_quantities(login_as, bad):
    """Reject non-positive or non-integer stock quantities with a 400 error."""
    alice = login_as("alice", 1)
    assert alice.post("/branches/1/stock/add", json={"product_id": "HB-LAP-1001", "quantity": bad}).status_code == 400


def test_cannot_operate_on_another_branch(login_as):
    """Block a common user from viewing or modifying stock in another branch."""
    alice = login_as("alice", 1)
    assert alice.post("/branches/2/stock/add", json={"product_id": "HB-LAP-1001", "quantity": 1}).status_code == 403
    assert alice.get("/branches/2/stock").status_code == 403


def test_unknown_product_rejected(login_as):
    """Return a 404 error when trying to add stock for a product ID not in the catalog."""
    alice = login_as("alice", 1)
    assert alice.post("/branches/1/stock/add", json={"product_id": "ZZZ", "quantity": 1}).status_code == 404


def test_admin_create_list_and_hide_hash(login_as):
    """Check that admins can create and list users without exposing password hashes."""
    admin = login_as("admin")
    admin.post("/admin/users", json={"username": "bob", "password": "password1", "branch_id": 2})
    users = admin.get("/admin/users").get_json()
    assert "bob" in [u["username"] for u in users] and all("password_hash" not in u for u in users)


def test_soft_delete(login_as, app):
    """Verify that soft-deleting a user blocks login while keeping their past stock history."""
    admin = login_as("admin")
    alice = login_as("alice", 1)
    alice.post("/branches/1/stock/add", json={"product_id": "HB-LAP-1001", "quantity": 1})
    uid = [u["id"] for u in admin.get("/admin/users").get_json() if u["username"] == "alice"][0]
    assert admin.delete(f"/admin/users/{uid}").status_code == 200
    assert alice.get("/branches/1/stock").status_code == 401
    assert app.test_client().post("/login", json={"username": "alice", "password": "password1"}).status_code == 401
    db = app.extensions["session_factory"]()
    assert db.get(Stock, (1, "HB-LAP-1001")).quantity == 11
    assert db.query(User).filter_by(username="alice").one().is_deleted is True
    db.close()


@pytest.mark.parametrize("method,url", [("get", "/branches/1/stock"), ("post", "/branches/1/stock/add")])
def test_admin_cannot_manage_stock(login_as, method, url):
    """Ensure admin accounts are forbidden from accessing or modifying branch stock."""
    admin = login_as("admin")
    assert getattr(admin, method)(url, json={"product_id": "HB-LAP-1001", "quantity": 1}).status_code == 403


def test_anonymous_and_common_cannot_manage_users(app, login_as):
    """Ensure anonymous and common users cannot access admin user-management routes."""
    assert app.test_client().get("/admin/users").status_code == 401
    assert login_as("alice", 1).get("/admin/users").status_code == 403


def test_password_hashing(app):
    """Verify that stored passwords are securely hashed with PBKDF2 instead of plain text."""
    db = app.extensions["session_factory"]()
    admin = db.query(User).filter_by(username="admin").one()
    assert "adminpass1" not in admin.password_hash and admin.password_hash.startswith("pbkdf2_sha256$")
    assert verify_password("adminpass1", admin.password_hash) and not verify_password("x", admin.password_hash)
    db.close()


def test_product_details_from_api(login_as):
    """Confirm that valid product IDs return details and unknown IDs return 404."""
    admin = login_as("admin")
    assert admin.get("/products/HB-LAP-1001").get_json()["name"] == "Laptop"
    assert admin.get("/products/ZZ").status_code == 404
