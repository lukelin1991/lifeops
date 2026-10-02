from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeightGoal(Base):
    __tablename__ = "weight_goals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    starting_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    goal_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="planned"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
