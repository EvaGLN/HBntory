"""
This module define the database schema for a multi-branch stock management
application, using SQLAlchemy 2.x (declarative ORM).
It describes three tables: branches, users and stock) as Python classes, and
provides two functions to connect to the database and create the tables.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import CheckConstraint, ForeignKey, Index, String, \
                       create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Class from which inherit all other models. It keeps in memory all
    declared table, which allow to create them.
    """

    pass


def utcnow():
    """
    Return the date and time from a specified time zone.
    """

    return datetime.now(timezone.utc)


class Branch(Base):
    """
    Create the 'branches' tables and add all needed column in it.
    """

    __tablename__ = "branches"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    # Create a link with other table column
    users: Mapped[list["User"]] = relationship(back_populates="branch")
    stock: Mapped[list["Stock"]] = relationship(back_populates="branch")


class User(Base):
    """
    Create the 'users' tables and add all needed column in it. Also apply
    constraint on some column to ensure the business layer.
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10))
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"))
    is_deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow,
                                                 onupdate=utcnow)
    branch: Mapped[Optional["Branch"]] = relationship(back_populates="users")

    __table_args__ = (
        # Enforce the role to be either admin or common
        CheckConstraint("role IN ('admin', 'common')", name="ck_users_role"),
        # Enforce the admin to not be linked to any branches and the opposite
        # for common role.
        CheckConstraint("(role = 'admin' AND branch_id IS NULL) OR " +
                        "(role = 'common' AND branch_id IS NOT NULL)",
                        name="ck_users_role_branch"
                        ),
    )


class Stock(Base):
    """
    Create the 'stocks' tables and add all needed column in it. Also apply
    constraint on some column to ensure the business layer.
    """
    __tablename__ = "stock"
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"),
                                           primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    quantity: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow,
                                                 onupdate=utcnow)
    branch: Mapped["Branch"] = relationship(back_populates="stock")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_stock_quantity"),
        # Create an index on the product_id, allowing the AI agent to browses
        # products quickly.
        Index("ix_stock_product", "product_id"),
    )


def make_engine(url):
    """
    Create engine, the entry point to the database.
    """

    return create_engine(url)


def create_tables(engine):
    """
    Iterate over all the classes inheriting from Base and execute CREATE TABLE
    for each none existing table.
    """

    Base.metadata.create_all(engine)
