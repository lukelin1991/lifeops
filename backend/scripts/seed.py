"""
Fill LifeOps with SAMPLE data so every page has something to show.

    cd backend
    python scripts/seed.py            # refuses if the DB already has data
    python scripts/seed.py --force    # add sample rows anyway

Everything created here is fake and marked "[SAMPLE]" (in notes, titles
or merchant names). Best used on a separate demo database, e.g.

    createdb -h localhost -U lifeops lifeops_demo
    DATABASE_URL=postgresql+psycopg://lifeops:lifeops@localhost:5432/lifeops_demo \
        alembic upgrade head
    DATABASE_URL=postgresql+psycopg://lifeops:lifeops@localhost:5432/lifeops_demo \
        python scripts/seed.py
"""

import argparse
import datetime
import sys
from decimal import Decimal
from pathlib import Path

# Make `import app` work when run as `python scripts/seed.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Account,
    Budget,
    CalendarEvent,
    Category,
    Certification,
    Contact,
    Debt,
    Holding,
    Interview,
    JobApplication,
    RecurringBill,
    Task,
    Transaction,
    WatchlistItem,
    WeightEntry,
    WeightGoal,
)
from app.services.dates import add_months, today  # noqa: E402

SAMPLE = "[SAMPLE]"


def d(value: str) -> Decimal:
    return Decimal(value)


def has_data(db) -> bool:
    for model in (WeightEntry, Transaction, CalendarEvent, Holding, JobApplication):
        if db.scalar(select(func.count()).select_from(model)):
            return True
    return False


def seed_health(db, current: datetime.date) -> None:
    if db.scalar(select(func.count()).select_from(WeightEntry)):
        print("  health: weight entries already exist, skipping")
        return

    weights = [262.4, 261.0, 260.2, 259.8, 258.1, 257.5, 256.9, 255.2, 254.8, 253.6]
    for weeks_ago, weight in zip(range(len(weights) - 1, -1, -1), weights, strict=True):
        db.add(WeightEntry(
            weight=weight,
            measurement_date=current - datetime.timedelta(weeks=weeks_ago),
        ))

    db.add(WeightGoal(
        starting_weight=262.0,
        goal_weight=220.0,
        status="active",
        activated_at=datetime.datetime.now() - datetime.timedelta(weeks=9),
    ))
    db.add(WeightGoal(starting_weight=220.0, goal_weight=200.0, status="planned"))


def seed_money(db, current: datetime.date) -> None:
    checking = Account(name=f"Checking {SAMPLE}", account_type="checking",
                       institution="Sample Bank", balance=d("3240.18"))
    savings = Account(name=f"Savings {SAMPLE}", account_type="savings",
                      institution="Sample Bank", balance=d("12500.00"))
    db.add_all([checking, savings])

    names = {
        "Groceries": "expense", "Dining Out": "expense", "Rent": "expense",
        "Utilities": "expense", "Transportation": "expense",
        "Subscriptions": "expense", "Fun": "expense", "Salary": "income",
    }
    categories = {}
    for name, kind in names.items():
        category = db.scalar(select(Category).where(Category.name == name))
        if category is None:
            category = Category(name=name, kind=kind)
            db.add(category)
        categories[name] = category
    db.flush()

    budgets = {
        "Groceries": "550", "Dining Out": "200", "Rent": "1850", "Utilities": "180",
        "Transportation": "250", "Subscriptions": "60", "Fun": "150",
    }
    for month_offset in (-1, 0):
        month = add_months(current.replace(day=1), month_offset)
        for name, amount in budgets.items():
            exists = db.scalar(select(Budget).where(
                Budget.category_id == categories[name].id,
                Budget.year == month.year, Budget.month == month.month,
            ))
            if exists is None:
                db.add(Budget(category_id=categories[name].id, year=month.year,
                              month=month.month, amount=d(amount)))

    first = current.replace(day=1)
    last_month = add_months(first, -1)
    rows = [
        # (date, type, amount, merchant, category)
        (last_month, "income", "3900.00", "Employer payroll", "Salary"),
        (last_month.replace(day=15), "income", "3900.00", "Employer payroll", "Salary"),
        (last_month.replace(day=1), "expense", "1850.00", "Landlord", "Rent"),
        (last_month.replace(day=4), "expense", "132.48", "Trader Joe's", "Groceries"),
        (last_month.replace(day=11), "expense", "164.20", "Whole Foods", "Groceries"),
        (last_month.replace(day=18), "expense", "58.75", "Thai Basil", "Dining Out"),
        (last_month.replace(day=21), "expense", "112.36", "Electric Co", "Utilities"),
        (last_month.replace(day=25), "expense", "45.00", "Gas station", "Transportation"),
        (first, "income", "3900.00", "Employer payroll", "Salary"),
        (first, "expense", "1850.00", "Landlord", "Rent"),
        (first.replace(day=min(2, current.day)), "expense", "15.49", "Netflix",
         "Subscriptions"),
        (current, "expense", "88.12", "Trader Joe's", "Groceries"),
        (current, "expense", "24.50", "Chipotle", "Dining Out"),
        (current, "expense", "180.00", "Concert tickets", "Fun"),
    ]
    for day, tx_type, amount, merchant, category in rows:
        db.add(Transaction(
            transaction_type=tx_type, amount=d(amount), transaction_date=day,
            merchant=f"{merchant} {SAMPLE}", category_id=categories[category].id,
            account_id=checking.id, notes=SAMPLE,
        ))

    bills = [
        ("Rent", "1850.00", 1, "monthly", False, "Rent"),
        ("Internet", "79.99", 12, "monthly", True, "Utilities"),
        ("Phone", "45.00", 18, "monthly", True, "Utilities"),
        ("Spotify", "11.99", 22, "monthly", True, "Subscriptions"),
        ("Car insurance", "612.00", 5, "quarterly", False, "Transportation"),
        ("Domain renewal", "18.00", 3, "yearly", True, "Subscriptions"),
    ]
    for name, amount, due_day, frequency, autopay, category in bills:
        db.add(RecurringBill(
            name=f"{name} {SAMPLE}", amount=d(amount), due_day=due_day,
            frequency=frequency, autopay=autopay,
            start_date=add_months(first, -2), category_id=categories[category].id,
            notes=SAMPLE,
        ))

    db.add_all([
        Debt(name=f"Visa {SAMPLE}", balance=d("3200.00"), apr=d("24.99"),
             minimum_payment=d("96.00"), notes=SAMPLE),
        Debt(name=f"Car loan {SAMPLE}", balance=d("11400.00"), apr=d("6.49"),
             minimum_payment=d("315.00"), notes=SAMPLE),
        Debt(name=f"Student loan {SAMPLE}", balance=d("18750.00"), apr=d("4.99"),
             minimum_payment=d("210.00"), notes=SAMPLE),
    ])


def seed_calendar(db, current: datetime.date) -> None:
    def at(day_offset: int, hour: int, minute: int = 0) -> datetime.datetime:
        day = current + datetime.timedelta(days=day_offset)
        return datetime.datetime.combine(day, datetime.time(hour, minute))

    db.add_all([
        CalendarEvent(title=f"Gym {SAMPLE}", start_at=at(0, 18), end_at=at(0, 19),
                      location="Downtown gym", notes=SAMPLE),
        CalendarEvent(title=f"Team standup {SAMPLE}", start_at=at(1, 9, 30),
                      end_at=at(1, 9, 45), location="Zoom", notes=SAMPLE),
        CalendarEvent(title=f"Dentist {SAMPLE}", start_at=at(3, 14), end_at=at(3, 15),
                      location="Smile Dental", notes=SAMPLE),
        CalendarEvent(title=f"Weekend trip {SAMPLE}", start_at=at(9, 0),
                      end_at=at(11, 23, 59), all_day=True, notes=SAMPLE),
    ])

    db.add_all([
        Task(title=f"Review Terraform module {SAMPLE}", due_date=current,
             priority="high", notes=SAMPLE),
        Task(title=f"Meal prep {SAMPLE}", due_date=current, priority="medium",
             recurrence="weekly", notes=SAMPLE),
        Task(title=f"Pay credit card {SAMPLE}", due_date=current - datetime.timedelta(days=1),
             priority="high", recurrence="monthly", notes=SAMPLE),
        Task(title=f"Renew passport {SAMPLE}", due_date=current + datetime.timedelta(days=20),
             priority="low", notes=SAMPLE),
    ])


def seed_invest(db) -> None:
    db.add_all([
        Holding(symbol="VTI", asset_type="stock", name="Vanguard Total Market",
                quantity=d("42"), avg_cost=d("221.40"), notes=SAMPLE),
        Holding(symbol="AAPL", asset_type="stock", name="Apple",
                quantity=d("15"), avg_cost=d("172.10"), notes=SAMPLE),
        Holding(symbol="MSFT", asset_type="stock", name="Microsoft",
                quantity=d("8"), avg_cost=d("318.75"), notes=SAMPLE),
        Holding(symbol="BTC", asset_type="crypto", name="Bitcoin",
                quantity=d("0.085"), avg_cost=d("41250"), notes=SAMPLE),
        Holding(symbol="ETH", asset_type="crypto", name="Ethereum",
                quantity=d("1.4"), avg_cost=d("2150"), notes=SAMPLE),
    ])
    db.add_all([
        WatchlistItem(symbol="NVDA", asset_type="stock", target_price=d("110"), notes=SAMPLE),
        WatchlistItem(symbol="AMZN", asset_type="stock", notes=SAMPLE),
        WatchlistItem(symbol="SOL", asset_type="crypto", target_price=d("120"), notes=SAMPLE),
    ])


def seed_career(db, current: datetime.date) -> None:
    def ago(days: int) -> datetime.date:
        return current - datetime.timedelta(days=days)

    apps = [
        JobApplication(company="Sample Cloud Co", title="DevOps Engineer",
                       salary_min=120000, salary_max=145000, location="Remote (US)",
                       work_mode="remote", status="interview", applied_date=ago(12),
                       url="https://example.com/jobs/1", notes=SAMPLE),
        JobApplication(company="Example Fintech", title="Site Reliability Engineer",
                       salary_min=135000, salary_max=160000, location="New York, NY",
                       work_mode="hybrid", status="screen", applied_date=ago(8), notes=SAMPLE),
        JobApplication(company="Demo Health", title="Cloud Engineer",
                       salary_min=115000, salary_max=130000, location="Boston, MA",
                       work_mode="onsite", status="applied", applied_date=ago(3), notes=SAMPLE),
        JobApplication(company="Placeholder AI", title="Platform Engineer",
                       work_mode="remote", status="rejected", applied_date=ago(30),
                       notes=SAMPLE),
        JobApplication(company="Fake Logistics", title="Junior DevOps Engineer",
                       salary_min=95000, salary_max=110000, work_mode="remote",
                       status="applied", applied_date=ago(1), notes=SAMPLE),
    ]
    db.add_all(apps)
    db.flush()

    db.add_all([
        Interview(application_id=apps[0].id, stage="recruiter_screen", outcome="passed",
                  scheduled_at=datetime.datetime.combine(ago(6), datetime.time(11)),
                  notes=SAMPLE),
        Interview(application_id=apps[0].id, stage="technical",
                  scheduled_at=datetime.datetime.combine(
                      current + datetime.timedelta(days=2), datetime.time(14)),
                  notes=f"{SAMPLE} Kubernetes + Terraform deep dive"),
        Interview(application_id=apps[1].id, stage="recruiter_screen",
                  scheduled_at=datetime.datetime.combine(
                      current + datetime.timedelta(days=5), datetime.time(10)),
                  notes=SAMPLE),
    ])
    db.add(Contact(name="Jordan Recruiter", company="Sample Cloud Co", role="Technical Recruiter",
                   email="jordan@example.com", application_id=apps[0].id, notes=SAMPLE))

    db.add_all([
        Certification(name="AWS Certified Solutions Architect - Associate", provider="AWS",
                      target_date=current + datetime.timedelta(days=45),
                      status="in_progress", notes=SAMPLE),
        Certification(name="Certified Kubernetes Administrator (CKA)", provider="CNCF",
                      target_date=current + datetime.timedelta(days=120), notes=SAMPLE),
        Certification(name="HashiCorp Terraform Associate", provider="HashiCorp",
                      status="completed", completed_date=current - datetime.timedelta(days=60),
                      notes=SAMPLE),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Add SAMPLE data to LifeOps.")
    parser.add_argument("--force", action="store_true",
                        help="add sample rows even if the database already has data")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if has_data(db) and not args.force:
            raise SystemExit(
                "This database already has data. Seed a separate demo database, "
                "or re-run with --force to add sample rows anyway."
            )

        current = today()
        print("Adding SAMPLE data...")
        seed_health(db, current)
        seed_money(db, current)
        seed_calendar(db, current)
        seed_invest(db)
        seed_career(db, current)
        db.commit()
        print("Done. Every sample row is marked [SAMPLE].")
    finally:
        db.close()


if __name__ == "__main__":
    main()
