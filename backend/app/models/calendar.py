import datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    end_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    all_day: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    location: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[datetime.date | None] = mapped_column(
        Date, index=True
    )
    # low | medium | high
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="medium"
    )
    # todo | in_progress | done
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="todo"
    )
    # none | daily | weekly | monthly
    recurrence: Mapped[str] = mapped_column(
        String(10), nullable=False, default="none"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )
