#!/usr/bin/python3
"""Manage user accounts, credentials and branch assignments."""

from sqlalchemy import select
from authentication import hash_password
from models import Branch, User


class UserError(ValueError):
    """Custom exception carrying an error code and message."""
    def __init__(self, code, message):
        # super() calls the parent class (ValueError) so it stores the error message normally
        super().__init__(message)
        self.code = code


def require_branch(session, branch_id):
    """Verify that branch_id is a valid integer matching a real branch."""
    if (not isinstance(branch_id, int) or isinstance(branch_id, bool)
            or session.get(Branch, branch_id) is None):
        raise UserError("branch_not_found", "unknown branch")


def list_users(session):
    """Return all active users sorted by their ID."""
    # scalars() (plural) extracts multiple objects directly from the query results
    return list(session.scalars(select(User).where(
        User.is_deleted.is_(False)).order_by(User.id)))


def create_user(session, username, password, branch_id):
    """Validate inputs and save a new common user in the database."""
    if (not isinstance(username, str) or not isinstance(password, str)
            or not username or len(password) < 8):
        raise UserError(
            "invalid_input", "username and password (8+ chars) are required")
    require_branch(session, branch_id)
    # scalar() (singular) extracts a single object from the query result or returns None
    if session.scalar(
            select(User).where(User.username == username)) is not None:
        raise UserError("username_taken", "username already used")
    user = User(username=username, password_hash=hash_password(
        password), role="common", branch_id=branch_id)
    session.add(user)
    session.commit()
    return user


def get_common_user(session, user_id):
    """Fetch an active common user or fail if admin or missing."""
    user = session.get(User, user_id)
    if user is None or user.is_deleted:
        raise UserError("user_not_found", "unknown user")
    if user.role == "admin":
        raise UserError("admin_protected", "the admin cannot be modified here")
    return user


def soft_delete_user(session, user_id):
    """Mark a common user as deleted without removing their row."""
    user = get_common_user(session, user_id)
    user.is_deleted = True
    session.commit()


def change_password(session, user_id, new_password):
    """Update a common user's password after checking its length."""
    if not isinstance(new_password, str) or len(new_password) < 8:
        raise UserError("invalid_input", "password must have 8+ chars")
    user = get_common_user(session, user_id)
    user.password_hash = hash_password(new_password)
    session.commit()


def change_branch(session, user_id, branch_id):
    """Reassign a common user to a different valid branch."""
    require_branch(session, branch_id)
    user = get_common_user(session, user_id)
    user.branch_id = branch_id
    session.commit()
