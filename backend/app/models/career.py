import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company: Mapped[str] = mapped_column(String(150), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    # Yearly salary range in USD
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(150))
    # remote | hybrid | onsite
    work_mode: Mapped[str] = mapped_column(
        String(10), nullable=False, default="remote"
    )
    # applied | screen | interview | offer | rejected | withdrawn
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="applied", index=True
    )
    applied_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False, default=datetime.date.today
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Interview(Base):
    __tablename__ = "job_interviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False
    )
    # e.g. recruiter_screen, technical, system_design, behavioral, final
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    # pending | passed | failed
    outcome: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Contact(Base):
    __tablename__ = "career_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    company: Mapped[str | None] = mapped_column(String(150))
    role: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    # Optional link to the application this person is connected to
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_applications.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class Certification(Base):
    """A certification or study goal, e.g. AWS SAA or CKA."""

    __tablename__ = "career_certifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100))
    target_date: Mapped[datetime.date | None] = mapped_column(Date)
    # planned | in_progress | completed
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="planned"
    )
    completed_date: Mapped[datetime.date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )
