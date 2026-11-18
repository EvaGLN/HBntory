"""
This module initialize the database by populating it whith provided data.
It create an admin account, two branche (Toulouse and Lyon), some stock
line and ensure that it's idempotent. It import some classes from models.py.
"""

import os
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from authentication import hash_password
from models import Branch, Stock, User, create_tables, make_engine

# Testing stocks to see if anythings wrong
SAMPLE_STOCK = [
    ("Toulouse", "P-001", 10), ("Toulouse", "P-002", 4),
    ("Lyon", "P-001", 2), ("Lyon", "P-003", 7)
]


def get_or_create_branch(session, name):
    """
    Looking for a branche by it's name and create it if it doesn't exists.
    """

    branch = session.scalar(select(Branch).where(Branch.name == name))
    if branch is None:
        branch = Branch(name=name)
        session.add(branch)
        session.flush()

    return branch


def seed(session, admin_password):
    """
    Handle the admin part. Check if the password is not less than 8 charaters.
    Also create an admin if one doesn't already exists.
    """

    if len(admin_password) < 8:
        raise ValueError("ADMIN_PASSWORD must have at least 8 characters")

    if session.scalar(select(User).where(User.username == "admin")) is None:
        session.add(User(username="admin",
                    password_hash=hash_password(admin_password),
                    role="admin"))

    for branch_name, product_id, quantity in SAMPLE_STOCK:
        branch = get_or_create_branch(session, branch_name)
        if session.get(Stock, (branch.id, product_id)) is None:
            session.add(Stock(branch_id=branch.id, product_id=product_id,
                         quantity=quantity))


if __name__ == "__main__":
    # Get the admin password from the environnement, no hard code.
    password = os.environ.get("ADMIN_PASSWORD")

    if not password:
        raise SystemExit("Set ADMIN_PASSWORD before running seed.py")

    engine = make_engine(os.environ.get("DATABASE_URL", "sqlite:///hbntory.db"))
    create_tables(engine)
    
    with sessionmaker(engine).begin() as session:
        seed(session, password)
