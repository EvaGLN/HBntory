#!/usr/bin/python3
"""Provide admin API endpoints to manage backoffice user accounts."""

from flask import Blueprint, jsonify, request
from authentication import admin_required
from dependencies import get_database
from user_service import (UserError, change_branch, change_password,
                          create_user, list_users, soft_delete_user)

# url_prefix="/admin" automatically puts "/admin" in front of every route in this file (e.g., "/admin/users")
bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS = {"invalid_input": 400, "branch_not_found": 404,
          "user_not_found": 404, "username_taken": 409, "admin_protected": 409}


def public(user):
    """Format a user object into a safe dictionary without the password."""
    return {"id": user.id, "username": user.username,
            "role": user.role, "branch_id": user.branch_id}


def fail(exc):
    """Build a JSON error response with the matching HTTP status code."""
    return jsonify(error=str(exc), code=exc.code), STATUS[exc.code]


@bp.get("/users")
@admin_required
def users_list():
    """Return all active user accounts as a JSON list."""
    return jsonify([public(u) for u in list_users(get_database())])


@bp.post("/users")
@admin_required
def users_create():
    """Register a new common user from the submitted JSON payload."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    try:
        user = create_user(get_database(), data.get("username"),
                           data.get("password"), data.get("branch_id"))
    except UserError as exc:
        return fail(exc)
    return jsonify(public(user)), 201


@bp.patch("/users/<int:user_id>/password")
@admin_required
def users_password(user_id):
    """Replace a user's password with a new one."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    try:
        change_password(get_database(), user_id, data.get("password"))
    except UserError as exc:
        return fail(exc)
    return jsonify(ok=True)


@bp.patch("/users/<int:user_id>/branch")
@admin_required
def users_branch(user_id):
    """Move a user account to a different branch."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    try:
        change_branch(get_database(), user_id, data.get("branch_id"))
    except UserError as exc:
        return fail(exc)
    return jsonify(ok=True)


@bp.delete("/users/<int:user_id>")
@admin_required
def users_delete(user_id):
    """Deactivate a user account via soft deletion."""
    try:
        soft_delete_user(get_database(), user_id)
    except UserError as exc:
        return fail(exc)
    return jsonify(ok=True)
