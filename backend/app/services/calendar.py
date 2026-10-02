import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.calendar import CalendarEvent, Task
from app.services.dates import add_months

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def next_occurrence(
    due: datetime.date,
    recurrence: str,
) -> datetime.date | None:
    """Next due date of a recurring task (None if it doesn't repeat)."""
    if recurrence == "daily":
        return due + datetime.timedelta(days=1)
    if recurrence == "weekly":
        return due + datetime.timedelta(weeks=1)
    if recurrence == "monthly":
        return add_months(due, 1)
    return None


def events_between(
    db: Session,
    start: datetime.date,
    end: datetime.date,
) -> list[CalendarEvent]:
    """Events that overlap [start 00:00, end 23:59:59]."""
    range_start = datetime.datetime.combine(start, datetime.time.min)
    range_end = datetime.datetime.combine(
        end + datetime.timedelta(days=1), datetime.time.min
    )

    return list(
        db.scalars(
            select(CalendarEvent)
            .where(
                CalendarEvent.start_at < range_end,
                func.coalesce(
                    CalendarEvent.end_at, CalendarEvent.start_at
                ) >= range_start,
            )
            .order_by(CalendarEvent.start_at)
        ).all()
    )


def open_tasks_between(
    db: Session,
    start: datetime.date,
    end: datetime.date,
) -> list[Task]:
    tasks = db.scalars(
        select(Task).where(
            Task.status != "done",
            Task.due_date.between(start, end),
        )
    ).all()
    return sort_tasks(tasks)


def overdue_tasks(db: Session, before: datetime.date) -> list[Task]:
    tasks = db.scalars(
        select(Task).where(
            Task.status != "done",
            Task.due_date < before,
        )
    ).all()
    return sort_tasks(tasks)


def sort_tasks(tasks) -> list[Task]:
    return sorted(
        tasks,
        key=lambda t: (
            t.due_date or datetime.date.max,
            PRIORITY_RANK.get(t.priority, 9),
            t.id,
        ),
    )


def build_agenda(
    db: Session,
    start: datetime.date,
    end: datetime.date,
    include_overdue: bool = True,
) -> dict:
    return {
        "start_date": start,
        "end_date": end,
        "events": events_between(db, start, end),
        "tasks": open_tasks_between(db, start, end),
        "overdue_tasks": overdue_tasks(db, start) if include_overdue else [],
    }

