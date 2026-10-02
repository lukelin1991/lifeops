import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.calendar import CalendarEvent, Task
from app.schemas.calendar import (
    Agenda,
    EventCreate,
    EventRead,
    EventUpdate,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.services import calendar as calendar_service
from app.services.crud import apply_update, get_or_404
from app.services.dates import now, today, week_bounds

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"]
)


# ---------------------------------------------------------
# EVENTS
# ---------------------------------------------------------

@router.get("/events")
def list_events(
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    if start_date and end_date:
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be on or after start_date"
            )
        events = calendar_service.events_between(db, start_date, end_date)
    else:
        query = select(CalendarEvent)
        if start_date:
            query = query.where(
                CalendarEvent.start_at
                >= datetime.datetime.combine(start_date, datetime.time.min)
            )
        if end_date:
            query = query.where(
                CalendarEvent.start_at
                < datetime.datetime.combine(
                    end_date + datetime.timedelta(days=1), datetime.time.min
                )
            )
        events = db.scalars(query.order_by(CalendarEvent.start_at)).all()

    return {"data": [EventRead.model_validate(e) for e in events]}


@router.post("/events", status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    item = CalendarEvent(**event.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Event created", "data": EventRead.model_validate(item)}


@router.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, CalendarEvent, event_id, "Event")
    return {"data": EventRead.model_validate(item)}


@router.patch("/events/{event_id}")
def update_event(
    event_id: int,
    event: EventUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, CalendarEvent, event_id, "Event")
    apply_update(item, event)

    if item.end_at and item.end_at < item.start_at:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="end_at must be after start_at"
        )

    db.commit()
    db.refresh(item)
    return {"message": "Event updated", "data": EventRead.model_validate(item)}


@router.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, CalendarEvent, event_id, "Event")
    db.delete(item)
    db.commit()
    return {"message": "Event deleted"}


# ---------------------------------------------------------
# TASKS
# ---------------------------------------------------------

@router.get("/tasks")
def list_tasks(
    status: Literal["todo", "in_progress", "done"] | None = None,
    include_done: bool = True,
    db: Session = Depends(get_db),
):
    query = select(Task)

    if status:
        query = query.where(Task.status == status)
    elif not include_done:
        query = query.where(Task.status != "done")

    tasks = calendar_service.sort_tasks(db.scalars(query).all())
    return {"data": [TaskRead.model_validate(t) for t in tasks]}


@router.post("/tasks", status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    if task.recurrence != "none" and task.due_date is None:
        raise HTTPException(
            status_code=400,
            detail="Recurring tasks need a due date"
        )

    item = Task(**task.model_dump())
    if item.status == "done":
        item.completed_at = now()

    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Task created", "data": TaskRead.model_validate(item)}


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Task, task_id, "Task")
    return {"data": TaskRead.model_validate(item)}


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Task, task_id, "Task")
    was_done = item.status == "done"

    apply_update(item, task)

    if item.recurrence != "none" and item.due_date is None:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Recurring tasks need a due date"
        )

    if item.status == "done" and not was_done:
        item.completed_at = now()
    elif item.status != "done":
        item.completed_at = None

    db.commit()
    db.refresh(item)
    return {"message": "Task updated", "data": TaskRead.model_validate(item)}


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Mark a task done. If it repeats, the next occurrence is created
    automatically with the next due date.
    """
    item = get_or_404(db, Task, task_id, "Task")

    if item.status == "done":
        raise HTTPException(
            status_code=400,
            detail="Task is already done"
        )

    item.status = "done"
    item.completed_at = now()

    next_task = None
    next_due = (
        calendar_service.next_occurrence(item.due_date, item.recurrence)
        if item.due_date
        else None
    )

    if next_due:
        next_task = Task(
            title=item.title,
            due_date=next_due,
            priority=item.priority,
            status="todo",
            recurrence=item.recurrence,
            notes=item.notes,
        )
        db.add(next_task)

    db.commit()
    db.refresh(item)
    if next_task:
        db.refresh(next_task)

    return {
        "message": "Task completed",
        "data": TaskRead.model_validate(item),
        "next_task": TaskRead.model_validate(next_task) if next_task else None,
    }


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Task, task_id, "Task")
    db.delete(item)
    db.commit()
    return {"message": "Task deleted"}


# ---------------------------------------------------------
# AGENDA
# ---------------------------------------------------------

@router.get("/agenda/today", response_model=Agenda)
def agenda_today(
    on: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    """Today's events and open tasks, plus anything overdue."""
    day = on or today()
    return calendar_service.build_agenda(db, day, day)


@router.get("/agenda/week", response_model=Agenda)
def agenda_week(
    on: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    """Monday-Sunday of the current week (or the week containing `on`)."""
    start, end = week_bounds(on or today())
    return calendar_service.build_agenda(db, start, end)


@router.get("/upcoming", response_model=Agenda)
def upcoming(
    days: int = Query(default=14, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Everything from today through the next `days` days."""
    start = today()
    end = start + datetime.timedelta(days=days)
    return calendar_service.build_agenda(db, start, end)
