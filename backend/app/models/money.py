"""
Money module tables.

Money is stored as Numeric (exact decimal) instead of Float so that
cents never drift: 0.1 + 0.2 really equals 0.3 here.
"""

import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    __tablename__ = "money_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # checking | savings | credit_card | cash | investment | other
    account_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="checking"
    )
    institution: Mapped[str | None] = mapped_column(String(100))
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Category(Base):
    __tablename__ = "money_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    # expense | income
    kind: Mapped[str] = mapped_column(
        String(10), nullable=False, default="expense"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Transaction(Base):
    __tablename__ = "money_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # income | expense
    transaction_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )
    # Always positive. transaction_type says which direction it went.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    transaction_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, index=True
    )
    merchant: Mapped[str | None] = mapped_column(String(150))
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("money_categories.id", ondelete="SET NULL"),
        index=True,
    )
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("money_accounts.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )

    category: Mapped[Category | None] = relationship()


class Budget(Base):
    """A monthly spending limit for one category."""

    __tablename__ = "money_budgets"
    __table_args__ = (
        UniqueConstraint(
            "category_id", "year", "month",
            name="uq_money_budgets_category_month",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("money_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )

    category: Mapped[Category] = relationship()


class RecurringBill(Base):
    __tablename__ = "money_recurring_bills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    # Day of the month the bill is due (1-31, clamped for short months)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    # monthly | quarterly | yearly
    frequency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="monthly"
    )
    # First month the bill applies. Quarterly/yearly bills repeat from here.
    start_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, default=datetime.date.today
    )
    autopay: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("money_categories.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Debt(Base):
    __tablename__ = "money_debts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    # Annual percentage rate, e.g. 22.99 means 22.99%
    apr: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False
    )
    minimum_payment: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )
