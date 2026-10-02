import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Priority = Literal["low", "medium", "high"]
TaskStatus = Literal["todo", "in_progress", "done"]
Recurrence = Literal["none", "daily", "weekly", "monthly"]


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    start_at: datetime.datetime
    end_at: datetime.datetime | None = None
    all_day: bool = False
    location: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def check_times(self):
        if self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    start_at: datetime.datetime | None = None
    end_at: datetime.datetime | None = None
    all_day: bool | None = None
    location: str | None = None
    notes: str | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    start_at: datetime.datetime
    end_at: datetime.datetime | None
    all_day: bool
    location: str | None
    notes: str | None
    created_at: datetime.datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_date: datetime.date | None = None
    priority: Priority = "medium"
    status: TaskStatus = "todo"
    recurrence: Recurrence = "none"
    notes: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_date: datetime.date | None = None
    priority: Priority | None = None
    status: TaskStatus | None = None
    recurrence: Recurrence | None = None
    notes: str | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    due_date: datetime.date | None
    priority: str
    status: str
    recurrence: str
    notes: str | None
    completed_at: datetime.datetime | None
    created_at: datetime.datetime


class Agenda(BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    events: list[EventRead]
    tasks: list[TaskRead]
    overdue_tasks: list[TaskRead]
