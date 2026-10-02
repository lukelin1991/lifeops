import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.money import (
    Account,
    Budget,
    Category,
    Debt,
    RecurringBill,
    Transaction,
)
from app.schemas.money import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    BillCreate,
    BillRead,
    BillUpdate,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    DebtCreate,
    DebtPayoffResult,
    DebtRead,
    DebtUpdate,
    MonthlySummary,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services import money as money_service
from app.services.crud import apply_update, get_or_404
from app.services.dates import add_months, today

router = APIRouter(
    prefix="/money",
    tags=["Money"]
)


def _commit_or_conflict(db: Session, detail: str) -> None:
    """Commit, turning a unique-constraint error into a 409."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail)


def _check_links(
    db: Session,
    category_id: int | None = None,
    account_id: int | None = None,
) -> None:
    if category_id is not None and db.get(Category, category_id) is None:
        raise HTTPException(status_code=400, detail="Category not found")

    if account_id is not None and db.get(Account, account_id) is None:
        raise HTTPException(status_code=400, detail="Account not found")


# ---------------------------------------------------------
# ACCOUNTS
# ---------------------------------------------------------

@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account).order_by(Account.name)).all()
    return {"data": [AccountRead.model_validate(a) for a in accounts]}


@router.post("/accounts", status_code=201)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    item = Account(**account.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Account created", "data": AccountRead.model_validate(item)}


@router.patch("/accounts/{account_id}")
def update_account(
    account_id: int,
    account: AccountUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Account, account_id, "Account")
    apply_update(item, account)
    db.commit()
    db.refresh(item)
    return {"message": "Account updated", "data": AccountRead.model_validate(item)}


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Account, account_id, "Account")
    db.delete(item)
    db.commit()
    return {"message": "Account deleted"}


# ---------------------------------------------------------
# CATEGORIES
# ---------------------------------------------------------

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    categories = db.scalars(select(Category).order_by(Category.name)).all()
    return {"data": [CategoryRead.model_validate(c) for c in categories]}


@router.post("/categories", status_code=201)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    item = Category(**category.model_dump())
    db.add(item)
    _commit_or_conflict(db, "A category with that name already exists")
    db.refresh(item)
    return {"message": "Category created", "data": CategoryRead.model_validate(item)}


@router.patch("/categories/{category_id}")
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Category, category_id, "Category")
    apply_update(item, category)
    _commit_or_conflict(db, "A category with that name already exists")
    db.refresh(item)
    return {"message": "Category updated", "data": CategoryRead.model_validate(item)}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    # Transactions keep existing (category becomes empty);
    # budgets for this category are removed with it.
    item = get_or_404(db, Category, category_id, "Category")
    db.delete(item)
    db.commit()
    return {"message": "Category deleted"}


# ---------------------------------------------------------
# TRANSACTIONS
# ---------------------------------------------------------

def _transaction_read(item: Transaction) -> TransactionRead:
    data = TransactionRead.model_validate(item)
    data.category_name = item.category.name if item.category else None
    return data


@router.get("/transactions")
def list_transactions(
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    category_id: int | None = None,
    transaction_type: Literal["income", "expense"] | None = None,
    account_id: int | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be on or after start_date"
        )

    query = select(Transaction)

    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)
    if transaction_type:
        query = query.where(Transaction.transaction_type == transaction_type)
    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)

    transactions = db.scalars(
        query.order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc(),
        ).limit(limit)
    ).all()

    return {"data": [_transaction_read(t) for t in transactions]}


@router.post("/transactions", status_code=201)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    _check_links(db, transaction.category_id, transaction.account_id)

    item = Transaction(**transaction.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Transaction recorded", "data": _transaction_read(item)}


@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Transaction, transaction_id, "Transaction")
    return {"data": _transaction_read(item)}


@router.patch("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Transaction, transaction_id, "Transaction")
    _check_links(db, transaction.category_id, transaction.account_id)
    apply_update(item, transaction)
    db.commit()
    db.refresh(item)
    return {"message": "Transaction updated", "data": _transaction_read(item)}


@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Transaction, transaction_id, "Transaction")
    db.delete(item)
    db.commit()
    return {"message": "Transaction deleted"}


# ---------------------------------------------------------
# BUDGETS (monthly, per category)
# ---------------------------------------------------------

def _budget_read(item: Budget) -> BudgetRead:
    data = BudgetRead.model_validate(item)
    data.category_name = item.category.name if item.category else None
    return data


@router.get("/budgets")
def list_budgets(
    year: int | None = None,
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
):
    query = select(Budget)

    if year is not None:
        query = query.where(Budget.year == year)
    if month is not None:
        query = query.where(Budget.month == month)

    budgets = db.scalars(
        query.order_by(Budget.year.desc(), Budget.month.desc(), Budget.id)
    ).all()
    return {"data": [_budget_read(b) for b in budgets]}


@router.post("/budgets", status_code=201)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    _check_links(db, category_id=budget.category_id)

    item = Budget(**budget.model_dump())
    db.add(item)
    _commit_or_conflict(
        db, "A budget for that category and month already exists"
    )
    db.refresh(item)
    return {"message": "Budget created", "data": _budget_read(item)}


@router.post("/budgets/copy", status_code=201)
def copy_budgets(
    from_year: int,
    from_month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
):
    """Copy one month's budgets into the following month (skips existing)."""
    source = db.scalars(
        select(Budget).where(
            Budget.year == from_year, Budget.month == from_month
        )
    ).all()

    target = add_months(datetime.date(from_year, from_month, 1), 1)
    existing = set(
        db.scalars(
            select(Budget.category_id).where(
                Budget.year == target.year, Budget.month == target.month
            )
        ).all()
    )

    created = []
    for budget in source:
        if budget.category_id in existing:
            continue
        item = Budget(
            category_id=budget.category_id,
            year=target.year,
            month=target.month,
            amount=budget.amount,
        )
        db.add(item)
        created.append(item)

    db.commit()
    return {
        "message": f"Copied {len(created)} budgets to {target:%Y-%m}",
        "data": [_budget_read(b) for b in created],
    }


@router.patch("/budgets/{budget_id}")
def update_budget(
    budget_id: int,
    budget: BudgetUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Budget, budget_id, "Budget")
    apply_update(item, budget)
    db.commit()
    db.refresh(item)
    return {"message": "Budget updated", "data": _budget_read(item)}


@router.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Budget, budget_id, "Budget")
    db.delete(item)
    db.commit()
    return {"message": "Budget deleted"}


# ---------------------------------------------------------
# RECURRING BILLS
# ---------------------------------------------------------

def _bill_read(item: RecurringBill) -> BillRead:
    data = BillRead.model_validate(item)
    data.next_due_date = money_service.next_due_date(item, today())
    return data


@router.get("/bills")
def list_bills(db: Session = Depends(get_db)):
    bills = db.scalars(select(RecurringBill)).all()
    data = [_bill_read(b) for b in bills]
    # Soonest first; inactive bills (no next date) at the end.
    data.sort(key=lambda b: (b.next_due_date is None, b.next_due_date or datetime.date.max, b.name))
    return {"data": data}


@router.post("/bills", status_code=201)
def create_bill(bill: BillCreate, db: Session = Depends(get_db)):
    _check_links(db, category_id=bill.category_id)

    values = bill.model_dump()
    values["start_date"] = values["start_date"] or today()

    item = RecurringBill(**values)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Bill created", "data": _bill_read(item)}


@router.get("/bills/{bill_id}")
def get_bill(bill_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, RecurringBill, bill_id, "Bill")
    return {"data": _bill_read(item)}


@router.patch("/bills/{bill_id}")
def update_bill(
    bill_id: int,
    bill: BillUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, RecurringBill, bill_id, "Bill")
    _check_links(db, category_id=bill.category_id)
    apply_update(item, bill)
    db.commit()
    db.refresh(item)
    return {"message": "Bill updated", "data": _bill_read(item)}


@router.delete("/bills/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, RecurringBill, bill_id, "Bill")
    db.delete(item)
    db.commit()
    return {"message": "Bill deleted"}


# ---------------------------------------------------------
# DEBTS
# ---------------------------------------------------------

@router.get("/debts")
def list_debts(db: Session = Depends(get_db)):
    debts = db.scalars(select(Debt).order_by(Debt.apr.desc())).all()
    return {"data": [DebtRead.model_validate(d) for d in debts]}


@router.post("/debts", status_code=201)
def create_debt(debt: DebtCreate, db: Session = Depends(get_db)):
    item = Debt(**debt.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Debt added", "data": DebtRead.model_validate(item)}


# Declared before /debts/{debt_id} so "payoff" isn't treated as an id.
@router.get("/debts/payoff", response_model=DebtPayoffResult)
def debt_payoff_projection(
    extra_payment: Decimal = Query(default=Decimal("0"), ge=0),
    strategy: Literal["avalanche", "snowball"] = "avalanche",
    db: Session = Depends(get_db),
):
    debts = db.scalars(select(Debt)).all()

    plan = money_service.project_debt_payoff(
        debts, extra_payment=extra_payment, strategy=strategy
    )
    baseline = money_service.project_debt_payoff(
        debts, extra_payment=Decimal("0"), strategy=strategy
    )

    payoff_month = None
    if plan.months_to_payoff:
        payoff_month = f"{add_months(today().replace(day=1), plan.months_to_payoff):%Y-%m}"

    interest_saved = None
    if plan.feasible and baseline.feasible:
        interest_saved = baseline.total_interest - plan.total_interest

    message = None
    if not plan.feasible:
        message = (
            "These payments never pay the debt off (they don't cover "
            "the interest). Increase the extra payment."
        )

    return DebtPayoffResult(
        strategy=plan.strategy,
        extra_payment=plan.extra_payment,
        monthly_payment=plan.monthly_payment,
        feasible=plan.feasible,
        months_to_payoff=plan.months_to_payoff,
        payoff_month=payoff_month,
        total_interest=plan.total_interest,
        total_paid=plan.total_paid,
        debts=plan.debts,
        baseline_months=baseline.months_to_payoff,
        baseline_total_interest=baseline.total_interest if baseline.feasible else None,
        interest_saved=interest_saved,
        message=message,
    )


@router.get("/debts/{debt_id}")
def get_debt(debt_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Debt, debt_id, "Debt")
    return {"data": DebtRead.model_validate(item)}


@router.patch("/debts/{debt_id}")
def update_debt(
    debt_id: int,
    debt: DebtUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Debt, debt_id, "Debt")
    apply_update(item, debt)
    db.commit()
    db.refresh(item)
    return {"message": "Debt updated", "data": DebtRead.model_validate(item)}


@router.delete("/debts/{debt_id}")
def delete_debt(debt_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Debt, debt_id, "Debt")
    db.delete(item)
    db.commit()
    return {"message": "Debt deleted"}


# ---------------------------------------------------------
# MONTHLY SUMMARY
# ---------------------------------------------------------

@router.get("/summary", response_model=MonthlySummary)
def get_monthly_summary(
    year: int | None = None,
    month: int | None = Query(default=None, ge=1, le=12),
    bills_before: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    """
    Income, spending and budget status for one month (default: this
    month), plus bills due from today until `bills_before`
    (default: 30 days from today).
    """
    current = today()
    year = year or current.year
    month = month or current.month
    bills_before = bills_before or current + datetime.timedelta(days=30)

    return money_service.monthly_summary(
        db,
        year=year,
        month=month,
        today=current,
        bills_before=bills_before,
    )
