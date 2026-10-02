from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # The calendar day this weight was measured.
    measurement_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # When this record was actually added to LifeOps.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )
