import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Holding(Base):
    __tablename__ = "invest_holdings"
    __table_args__ = (
        UniqueConstraint(
            "symbol", "asset_type",
            name="uq_invest_holdings_symbol_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Stored upper-case, e.g. AAPL or BTC
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    # stock | crypto
    asset_type: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    # Crypto needs fractional quantities, so allow 8 decimal places.
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False
    )
    # Average cost per unit
    avg_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class WatchlistItem(Base):
    __tablename__ = "invest_watchlist"
    __table_args__ = (
        UniqueConstraint(
            "symbol", "asset_type",
            name="uq_invest_watchlist_symbol_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(10), nullable=False)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.now
    )
