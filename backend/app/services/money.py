"""
Money calculations that are more than simple CRUD:

- when is a recurring bill due next?
- how long until my debts are paid off?
- how did this month go versus my budget?
"""

import datetime
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.money import (
    Budget,
    Category,
    Debt,
    RecurringBill,
    Transaction,
)
from app.services.dates import add_months, month_bounds

CENT = Decimal("0.01")
ZERO = Decimal("0")

FREQUENCY_MONTHS = {
    "monthly": 1,
    "quarterly": 3,
    "yearly": 12,
}


def to_cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------
# RECURRING BILLS
# ---------------------------------------------------------

def bill_due_dates(
    bill: RecurringBill,
    start: datetime.date,
    end: datetime.date,
) -> list[datetime.date]:
    """
    Every due date of a bill between start and end (both inclusive).

    A bill repeats every 1/3/12 months counting from the month of its
    start_date, always on due_day (clamped, so 31 -> Feb 28).
    """
    if not bill.is_active or end < start:
        return []

    step = FREQUENCY_MONTHS[bill.frequency]
    anchor = bill.start_date.replace(day=1)

    # Jump close to `start` instead of walking month by month from
    # an old start_date.
    months_since_anchor = (
        (start.year - anchor.year) * 12 + (start.month - anchor.month)
    )
    k = max(0, months_since_anchor // step - 1)

    dates = []

    while True:
        due = add_months(anchor, k * step, day=bill.due_day)
        k += 1

        if due > end:
            break

        if due < bill.start_date or due < start:
            continue

        dates.append(due)

    return dates


def next_due_date(
    bill: RecurringBill,
    on_or_after: datetime.date,
) -> datetime.date | None:
    dates = bill_due_dates(
        bill,
        on_or_after,
        on_or_after + datetime.timedelta(days=400),
    )
    return dates[0] if dates else None


# ---------------------------------------------------------
# DEBT PAYOFF PROJECTION
# ---------------------------------------------------------

@dataclass
class _DebtState:
    debt_id: int
    name: str
    apr: Decimal
    minimum_payment: Decimal
    starting_balance: Decimal
    balance: Decimal
    interest_paid: Decimal = ZERO
    payoff_month: int | None = None
    order: int = 0


@dataclass
class PayoffProjection:
    strategy: str
    extra_payment: Decimal
    monthly_payment: Decimal
    feasible: bool
    months_to_payoff: int | None
    total_interest: Decimal
    total_paid: Decimal
    debts: list[dict] = field(default_factory=list)


def project_debt_payoff(
    debts: list[Debt],
    extra_payment: Decimal = ZERO,
    strategy: str = "avalanche",
    max_months: int = 600,
) -> PayoffProjection:
    """
    Month-by-month simulation of paying off every debt.

    Each month:
      1. interest is added to every balance (APR / 12),
      2. every debt gets its minimum payment,
      3. whatever is left of the monthly budget (the extra payment plus
         minimums freed up by debts already paid off) goes to the
         target debt: highest APR first for "avalanche", smallest
         balance first for "snowball".

    The monthly budget stays the same for the whole simulation, which
    is what makes the "rollover" snowball effect happen.
    """
    states = [
        _DebtState(
            debt_id=debt.id,
            name=debt.name,
            apr=Decimal(debt.apr),
            minimum_payment=Decimal(debt.minimum_payment),
            starting_balance=Decimal(debt.balance),
            balance=Decimal(debt.balance),
        )
        for debt in debts
        if Decimal(debt.balance) > 0
    ]

    if strategy == "snowball":
        ordered = sorted(states, key=lambda d: (d.balance, -d.apr))
    else:
        ordered = sorted(states, key=lambda d: (-d.apr, d.balance))

    for position, state in enumerate(ordered, start=1):
        state.order = position

    monthly_budget = (
        sum((d.minimum_payment for d in states), ZERO) + extra_payment
    )

    month = 0
    feasible = True

    while any(d.balance > 0 for d in states):
        if month >= max_months:
            feasible = False
            break

        month += 1
        balance_before = sum((d.balance for d in states), ZERO)

        # 1. Interest
        for d in states:
            if d.balance > 0:
                interest = to_cents(d.balance * d.apr / Decimal(1200))
                d.balance += interest
                d.interest_paid += interest

        available = monthly_budget

        # 2. Minimum payments
        for d in states:
            if d.balance > 0 and available > 0:
                payment = min(d.minimum_payment, d.balance, available)
                d.balance -= payment
                available -= payment

        # 3. Extra (and rolled-over) money to the target debt(s)
        for d in ordered:
            if available <= 0:
                break
            if d.balance > 0:
                payment = min(available, d.balance)
                d.balance -= payment
                available -= payment

        for d in states:
            if d.balance <= 0 and d.payoff_month is None:
                d.payoff_month = month

        # Payments don't even cover the interest: it never ends.
        balance_after = sum((d.balance for d in states), ZERO)
        if balance_after >= balance_before:
            feasible = False
            break

    total_interest = sum((d.interest_paid for d in states), ZERO)
    total_start = sum((d.starting_balance for d in states), ZERO)

    return PayoffProjection(
        strategy=strategy,
        extra_payment=extra_payment,
        monthly_payment=monthly_budget,
        feasible=feasible,
        months_to_payoff=month if feasible else None,
        total_interest=total_interest,
        total_paid=total_start + total_interest,
        debts=[
            {
                "debt_id": d.debt_id,
                "name": d.name,
                "order": d.order,
                "starting_balance": d.starting_balance,
                "apr": d.apr,
                "months_to_payoff": d.payoff_month,
                "interest_paid": d.interest_paid,
            }
            for d in ordered
        ],
    )


# ---------------------------------------------------------
# MONTHLY SUMMARY
# ---------------------------------------------------------

def upcoming_bills(
    db: Session,
    start: datetime.date,
    before: datetime.date,
) -> list[dict]:
    """Every bill occurrence from start up to (not including) before."""
    bills = db.scalars(
        select(RecurringBill).where(RecurringBill.is_active.is_(True))
    ).all()

    occurrences = []

    for bill in bills:
        for due in bill_due_dates(
            bill, start, before - datetime.timedelta(days=1)
        ):
            occurrences.append({
                "bill_id": bill.id,
                "name": bill.name,
                "amount": bill.amount,
                "due_date": due,
                "autopay": bill.autopay,
            })

    occurrences.sort(key=lambda item: (item["due_date"], item["name"]))
    return occurrences


def monthly_summary(
    db: Session,
    year: int,
    month: int,
    today: datetime.date,
    bills_before: datetime.date,
) -> dict:
    first_day, last_day = month_bounds(year, month)

    totals = dict(
        db.execute(
            select(
                Transaction.transaction_type,
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .where(Transaction.transaction_date.between(first_day, last_day))
            .group_by(Transaction.transaction_type)
        ).all()
    )
    income = Decimal(totals.get("income", 0))
    spending = Decimal(totals.get("expense", 0))

    # Spending per category this month
    spent_rows = db.execute(
        select(
            Transaction.category_id,
            func.sum(Transaction.amount),
        )
        .where(
            Transaction.transaction_type == "expense",
            Transaction.transaction_date.between(first_day, last_day),
        )
        .group_by(Transaction.category_id)
    ).all()
    spent_by_category = {
        category_id: Decimal(total) for category_id, total in spent_rows
    }

    budgets = {
        budget.category_id: Decimal(budget.amount)
        for budget in db.scalars(
            select(Budget).where(Budget.year == year, Budget.month == month)
        ).all()
    }

    category_names = {
        category.id: category.name
        for category in db.scalars(select(Category)).all()
    }

    by_category = []
    for category_id in set(spent_by_category) | set(budgets):
        spent = spent_by_category.get(category_id, ZERO)
        budget = budgets.get(category_id)
        by_category.append({
            "category_id": category_id,
            "category_name": category_names.get(
                category_id, "Uncategorized"
            ),
            "spent": spent,
            "budget": budget,
            "remaining": budget - spent if budget is not None else None,
            "over_budget": budget is not None and spent > budget,
        })

    by_category.sort(key=lambda row: (-row["spent"], row["category_name"]))

    total_budget = sum(budgets.values(), ZERO)
    bills = upcoming_bills(db, today, bills_before)

    return {
        "year": year,
        "month": month,
        "income": income,
        "spending": spending,
        "net": income - spending,
        "total_budget": total_budget,
        "budget_remaining": total_budget - spending,
        "by_category": by_category,
        "upcoming_bills": bills,
        "upcoming_bills_total": sum(
            (bill["amount"] for bill in bills), ZERO
        ),
        "bills_before": bills_before,
    }
