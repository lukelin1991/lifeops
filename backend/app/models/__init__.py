# Import every model here so Base.metadata knows about all tables.
# Alembic (alembic/env.py) and the tests import this package.
from app.models.calendar import CalendarEvent, Task
from app.models.career import (
    Certification,
    Contact,
    Interview,
    JobApplication,
)
from app.models.invest import Holding, WatchlistItem
from app.models.money import (
    Account,
    Budget,
    Category,
    Debt,
    RecurringBill,
    Transaction,
)
from app.models.weight import WeightEntry
from app.models.weight_goal import WeightGoal

__all__ = [
    "Account",
    "Budget",
    "CalendarEvent",
    "Category",
    "Certification",
    "Contact",
    "Debt",
    "Holding",
    "Interview",
    "JobApplication",
    "RecurringBill",
    "Task",
    "Transaction",
    "WatchlistItem",
    "WeightEntry",
    "WeightGoal",
]
