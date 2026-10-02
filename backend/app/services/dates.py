import calendar
import datetime
from zoneinfo import ZoneInfo

from app.config import settings


def today() -> datetime.date:
    """Today's date in Luke's timezone (APP_TIMEZONE), not the server's."""
    return datetime.datetime.now(ZoneInfo(settings.timezone)).date()


def now() -> datetime.datetime:
    """Current local wall-clock time as a naive datetime."""
    return datetime.datetime.now(ZoneInfo(settings.timezone)).replace(
        tzinfo=None
    )


def clamp_day(year: int, month: int, day: int) -> datetime.date:
    """Day 31 in a 30-day month becomes the 30th (Feb -> 28/29)."""
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(day, last_day))


def add_months(
    value: datetime.date,
    months: int,
    day: int | None = None,
) -> datetime.date:
    """Move a date by N months, keeping the day where possible."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return clamp_day(year, month, day or value.day)


def month_bounds(year: int, month: int) -> tuple[datetime.date, datetime.date]:
    """First and last day of a month."""
    first = datetime.date(year, month, 1)
    last = clamp_day(year, month, 31)
    return first, last


def week_bounds(value: datetime.date) -> tuple[datetime.date, datetime.date]:
    """Monday..Sunday of the week containing value."""
    monday = value - datetime.timedelta(days=value.weekday())
    return monday, monday + datetime.timedelta(days=6)
