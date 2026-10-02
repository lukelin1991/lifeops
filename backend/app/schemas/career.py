import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

WorkMode = Literal["remote", "hybrid", "onsite"]
ApplicationStatus = Literal[
    "applied", "screen", "interview", "offer", "rejected", "withdrawn"
]
InterviewOutcome = Literal["pending", "passed", "failed"]
CertificationStatus = Literal["planned", "in_progress", "completed"]

APPLICATION_STATUSES = list(ApplicationStatus.__args__)


# ---------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------

class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=150)
    title: str = Field(min_length=1, max_length=150)
    url: str | None = Field(default=None, max_length=500)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    location: str | None = None
    work_mode: WorkMode = "remote"
    status: ApplicationStatus = "applied"
    applied_date: datetime.date | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def check_salary(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("salary_max must be >= salary_min")
        return self


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=150)
    title: str | None = Field(default=None, min_length=1, max_length=150)
    url: str | None = Field(default=None, max_length=500)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    location: str | None = None
    work_mode: WorkMode | None = None
    status: ApplicationStatus | None = None
    applied_date: datetime.date | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    title: str
    url: str | None
    salary_min: int | None
    salary_max: int | None
    location: str | None
    work_mode: str
    status: str
    applied_date: datetime.date
    notes: str | None
    created_at: datetime.datetime


# ---------------------------------------------------------
# INTERVIEWS
# ---------------------------------------------------------

class InterviewCreate(BaseModel):
    application_id: int
    scheduled_at: datetime.datetime
    stage: str = Field(min_length=1, max_length=50)
    outcome: InterviewOutcome = "pending"
    notes: str | None = None


class InterviewUpdate(BaseModel):
    scheduled_at: datetime.datetime | None = None
    stage: str | None = Field(default=None, min_length=1, max_length=50)
    outcome: InterviewOutcome | None = None
    notes: str | None = None


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    scheduled_at: datetime.datetime
    stage: str
    outcome: str
    notes: str | None
    created_at: datetime.datetime
    company: str | None = None
    title: str | None = None


# ---------------------------------------------------------
# CONTACTS
# ---------------------------------------------------------

class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    company: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    application_id: int | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    company: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    application_id: int | None = None
    notes: str | None = None


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str | None
    role: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    application_id: int | None
    notes: str | None
    created_at: datetime.datetime


# ---------------------------------------------------------
# CERTIFICATIONS / STUDY GOALS
# ---------------------------------------------------------

class CertificationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    provider: str | None = None
    target_date: datetime.date | None = None
    status: CertificationStatus = "planned"
    completed_date: datetime.date | None = None
    notes: str | None = None


class CertificationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    provider: str | None = None
    target_date: datetime.date | None = None
    status: CertificationStatus | None = None
    completed_date: datetime.date | None = None
    notes: str | None = None


class CertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider: str | None
    target_date: datetime.date | None
    status: str
    completed_date: datetime.date | None
    notes: str | None
    created_at: datetime.datetime


# ---------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------

class Pipeline(BaseModel):
    counts: dict[str, int]
    total: int
    active: int
    response_rate: float | None
    upcoming_interviews: list[InterviewRead]
