"""
GET /dashboard: one call that gives the frontend a snapshot of every
module. Each section reuses the same functions the module routers use.
"""

import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invest import Holding
from app.models.weight import WeightEntry
from app.routers.career import pipeline_summary
from app.routers.health import get_weight_progress
from app.schemas.calendar import EventRead, TaskRead
from app.schemas.invest import PortfolioSummary
from app.schemas.money import CategorySpending, UpcomingBill
from app.services import calendar as calendar_service
from app.services import money as money_service
from app.services.dates import today
from app.services.market_data import MarketDataService, get_market_data
from app.services.portfolio import build_portfolio

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Dashboard"]
)


def _health_section(db: Session) -> dict:
    latest = db.scalars(
        select(WeightEntry).order_by(
            WeightEntry.measurement_date.desc(),
            WeightEntry.created_at.desc(),
            WeightEntry.id.desc(),
        )
    ).first()

    # Reuse the Health router's own progress calculation.
    # It raises 404 when there is no active goal or no weights yet.
    try:
        progress = get_weight_progress(db=db)
    except HTTPException:
        progress = None

    return {
        "latest_weight": latest.weight if latest else None,
        "latest_measurement_date": latest.measurement_date if latest else None,
        "goal_progress": progress,
    }


def _money_section(db: Session, current: datetime.date) -> dict:
    summary = money_service.monthly_summary(
        db,
        year=current.year,
        month=current.month,
        today=current,
        bills_before=current + datetime.timedelta(days=14),
    )

    return {
        "year": summary["year"],
        "month": summary["month"],
        "income": summary["income"],
        "spending": summary["spending"],
        "total_budget": summary["total_budget"],
        "budget_remaining": summary["budget_remaining"],
        "over_budget_categories": [
            CategorySpending(**row)
            for row in summary["by_category"]
            if row["over_budget"]
        ],
        "upcoming_bills": [
            UpcomingBill(**bill) for bill in summary["upcoming_bills"]
        ],
        "upcoming_bills_total": summary["upcoming_bills_total"],
    }


def _calendar_section(db: Session, current: datetime.date) -> dict:
    agenda = calendar_service.build_agenda(db, current, current)

    return {
        "date": current,
        "events": [EventRead.model_validate(e) for e in agenda["events"]],
        "tasks": [TaskRead.model_validate(t) for t in agenda["tasks"]],
        "overdue_tasks": [
            TaskRead.model_validate(t) for t in agenda["overdue_tasks"]
        ],
    }


def _invest_section(db: Session, market: MarketDataService) -> dict:
    holdings = db.scalars(select(Holding)).all()

    try:
        prices = market.get_prices(
            [(h.symbol, h.asset_type) for h in holdings]
        )
        portfolio = build_portfolio(holdings, prices)
    except Exception:
        # The market service shouldn't raise, but the dashboard must
        # never fail because of prices.
        logger.exception("Portfolio section failed")
        return {"status": "unavailable", "summary": None}

    return {
        "status": "ok" if portfolio["summary"]["complete"] else "partial",
        "summary": PortfolioSummary(**portfolio["summary"]),
    }


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    market: MarketDataService = Depends(get_market_data),
):
    current = today()

    return {
        "date": current,
        "health": _health_section(db),
        "money": _money_section(db, current),
        "calendar": _calendar_section(db, current),
        "invest": _invest_section(db, market),
        "career": pipeline_summary(db),
    }
