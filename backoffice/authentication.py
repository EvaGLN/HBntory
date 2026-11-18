#!/usr/bin/python3
"""Handle user security, credential check and route permissions.
PBKDF2: Password-Based Key Derivation Function 2"""

from sqlalchemy import select
from models import User
# 'wraps' preserves the original function's name and docstring when creating a decorator.
# Without it, Flask gets confused because every decorated route would look like 'wrapper'.
from functools import wraps
from flask import g, jsonify, session
from dependencies import get_database

# 'hashlib' scrambles passwords into irreversible hashes (like PBKDF2-SHA256).
import hashlib
# 'hmac' compares two secret strings safely without leaking timing clues to hackers.
import hmac
# 'os' talks to the operating system to generate true random bytes for the password salt.
import os

ITERATIONS = 600_000


def authenticate(database, username, password):
    """Find a user in the database and verify their login credentials."""
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    # '.scalar()' runs the query and extracts a single result directly: the object or None.
    user = database.scalar(select(User).where(User.username == username))
    if user is None or user.is_deleted:
        # Run a fake password check so failed logins always take the same time to prevent finding usernames.
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def hash_password(password):
    """Turn a readable password into a secure scrambled string for storage."""
    # 'os.urandom(16)' asks the operating system for 16 random bytes.
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


DUMMY_HASH = hash_password("dummy")


def verify_password(password, stored):
    """Check if a typed password matches the scrambled version stored in the database."""
    try:
        method, iterations, salt_hex, digest_hex = stored.split("$")
        if method != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        iterations = int(iterations)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest.hex(), digest_hex)


def current_user():
    """Retrieve the active user profile from the current browser session."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = get_database().get(User, user_id)
    if user is None or user.is_deleted:
        return None
    return user


def login_required(view):
    """Block access to a route if the user is not signed in."""
    # Copy the original 'view' function's name and metadata onto 'wrapper' so Flask can identify the route.
    @wraps(view)
    # '*args' collects extra positional arguments as a tuple; '**kwargs' collects keyword arguments as a dictionary.
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify(error="authentication required"), 401
        g.user = user
        return view(*args, **kwargs)
    return wrapper


# Decorator factory: takes a 'role' argument and builds a custom decorator for it.
def role_required(role):
    """Restrict a route to signed-in users who have a specific permission level."""
    # Actual decorator: receives the Flask route function ('view') and wraps it.
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if g.user.role != role:
                return jsonify(error="forbidden"), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator


admin_required = role_required("admin")
common_required = role_required("common")
