#!/usr/bin/python3
"""Handle user sign-in and sign-out API endpoints for the backoffice."""

from flask import Blueprint, jsonify, request, session
from authentication import authenticate
from dependencies import get_database

# 'Blueprint' splits routes into separate themed files instead of putting everything in one giant app.py.
# '__name__' tells Flask which file this module lives in so the main app can plug it in later.
bp = Blueprint("authentication", __name__)


@bp.post("/login")
def login():
    """Verify submitted credentials and start a new browser session for the user."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    user = authenticate(
        get_database(), data.get("username", ""), data.get("password", ""))
    if user is None:
        return jsonify(error="invalid credentials"), 401
    # Wipe any existing session data before logging in to prevent session fixation attacks.
    session.clear()
    session["user_id"] = user.id
    return jsonify(
        username=user.username, role=user.role, branch_id=user.branch_id)


@bp.post("/logout")
def logout():
    """Clear the active browser session to sign out the current user."""
    session.clear()
    return jsonify(ok=True)
