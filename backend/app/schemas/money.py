import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Money

AccountType = Literal[
    "checking", "savings", "credit_card", "cash", "investment", "other"
]
CategoryKind = Literal["expense", "income"]
TransactionType = Literal["income", "expense"]
BillFrequency = Literal["monthly", "quarterly", "yearly"]


# ---------------------------------------------------------
# ACCOUNTS
# ---------------------------------------------------------

class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: AccountType = "checking"
    institution: str | None = None
    balance: Decimal = Decimal("0")


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    account_type: AccountType | None = None
    institution: str | None = None
    balance: Decimal | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type: str
    institution: str | None
    balance: Money
    created_at: datetime.datetime


# ---------------------------------------------------------
# CATEGORIES
# ---------------------------------------------------------

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: CategoryKind = "expense"


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    kind: CategoryKind | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str
    created_at: datetime.datetime


# ---------------------------------------------------------
# TRANSACTIONS
# ---------------------------------------------------------

class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    transaction_date: datetime.date
    merchant: str | None = None
    category_id: int | None = None
    account_id: int | None = None
    notes: str | None = None


class TransactionUpdate(BaseModel):
    transaction_type: TransactionType | None = None
    amount: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    transaction_date: datetime.date | None = None
    merchant: str | None = None
    category_id: int | None = None
    account_id: int | None = None
    notes: str | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    amount: Money
    transaction_date: datetime.date
    merchant: str | None
    category_id: int | None
    category_name: str | None = None
    account_id: int | None
    notes: str | None
    created_at: datetime.datetime


# ---------------------------------------------------------
# BUDGETS
# ---------------------------------------------------------

class BudgetCreate(BaseModel):
    category_id: int
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class BudgetUpdate(BaseModel):
    amount: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category_name: str | None = None
    year: int
    month: int
    amount: Money
    created_at: datetime.datetime


# ---------------------------------------------------------
# RECURRING BILLS
# ---------------------------------------------------------

class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    due_day: int = Field(ge=1, le=31)
    frequency: BillFrequency = "monthly"
    start_date: datetime.date | None = None
    autopay: bool = False
    is_active: bool = True
    category_id: int | None = None
    notes: str | None = None


class BillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    amount: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    due_day: int | None = Field(default=None, ge=1, le=31)
    frequency: BillFrequency | None = None
    start_date: datetime.date | None = None
    autopay: bool | None = None
    is_active: bool | None = None
    category_id: int | None = None
    notes: str | None = None


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: Money
    due_day: int
    frequency: str
    start_date: datetime.date
    autopay: bool
    is_active: bool
    category_id: int | None
    notes: str | None
    created_at: datetime.datetime
    next_due_date: datetime.date | None = None


# ---------------------------------------------------------
# DEBTS
# ---------------------------------------------------------

class DebtCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    balance: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    apr: Decimal = Field(ge=0, le=100, max_digits=6, decimal_places=3)
    minimum_payment: Decimal = Field(
        ge=0, max_digits=12, decimal_places=2
    )
    notes: str | None = None


class DebtUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    balance: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    apr: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=6, decimal_places=3
    )
    minimum_payment: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    notes: str | None = None


class DebtRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: Money
    apr: Money
    minimum_payment: Money
    notes: str | None
    created_at: datetime.datetime


class DebtPayoffItem(BaseModel):
    debt_id: int
    name: str
    order: int
    starting_balance: Money
    apr: Money
    months_to_payoff: int | None
    interest_paid: Money


class DebtPayoffResult(BaseModel):
    strategy: str
    extra_payment: Money
    monthly_payment: Money
    feasible: bool
    months_to_payoff: int | None
    payoff_month: str | None
    total_interest: Money
    total_paid: Money
    debts: list[DebtPayoffItem]
    baseline_months: int | None = None
    baseline_total_interest: Money | None = None
    interest_saved: Money | None = None
    message: str | None = None


# ---------------------------------------------------------
# MONTHLY SUMMARY
# ---------------------------------------------------------

class CategorySpending(BaseModel):
    category_id: int | None
    category_name: str
    spent: Money
    budget: Money | None
    remaining: Money | None
    over_budget: bool


class UpcomingBill(BaseModel):
    bill_id: int
    name: str
    amount: Money
    due_date: datetime.date
    autopay: bool


class MonthlySummary(BaseModel):
    year: int
    month: int
    income: Money
    spending: Money
    net: Money
    total_budget: Money
    budget_remaining: Money
    by_category: list[CategorySpending]
    upcoming_bills: list[UpcomingBill]
    upcoming_bills_total: Money
    bills_before: datetime.date

