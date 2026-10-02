import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Money

AssetType = Literal["stock", "crypto"]

# ok              -> live (or <60s cached) price
# missing_api_key -> the API key for this asset type isn't configured
# not_found       -> the provider doesn't know this symbol
# unavailable     -> network error, timeout, rate limit, bad key...
PriceStatus = Literal["ok", "missing_api_key", "not_found", "unavailable"]


def _clean_symbol(value: str) -> str:
    value = value.strip().upper()
    if not value:
        raise ValueError("symbol is required")
    return value


class HoldingCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    asset_type: AssetType
    name: str | None = None
    quantity: Decimal = Field(gt=0)
    avg_cost: Decimal = Field(ge=0)
    notes: str | None = None

    _symbol = field_validator("symbol")(_clean_symbol)


class HoldingUpdate(BaseModel):
    name: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    avg_cost: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class HoldingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    asset_type: str
    name: str | None
    quantity: Money
    avg_cost: Money
    notes: str | None
    created_at: datetime.datetime


class WatchlistCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    asset_type: AssetType
    target_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None

    _symbol = field_validator("symbol")(_clean_symbol)


class WatchlistUpdate(BaseModel):
    target_price: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    asset_type: str
    target_price: Money | None
    notes: str | None
    created_at: datetime.datetime


class Quote(BaseModel):
    symbol: str
    asset_type: str
    price: Money | None
    price_status: PriceStatus
    source: str | None = None
    message: str | None = None


class WatchlistWithPrice(WatchlistRead):
    price: Money | None
    price_status: PriceStatus
    price_message: str | None = None
    below_target: bool | None = None


class PricedHolding(HoldingRead):
    price: Money | None
    price_status: PriceStatus
    price_message: str | None = None
    cost_basis: Money
    market_value: Money | None
    gain_loss: Money | None
    gain_loss_pct: Money | None


class AllocationSlice(BaseModel):
    asset_type: str
    market_value: Money
    percent: Money


class PortfolioSummary(BaseModel):
    market_value: Money
    cost_basis: Money
    priced_cost_basis: Money
    gain_loss: Money
    gain_loss_pct: Money | None
    allocation: list[AllocationSlice]
    holdings_count: int
    priced_count: int
    unpriced_count: int
    complete: bool


class Portfolio(BaseModel):
    holdings: list[PricedHolding]
    summary: PortfolioSummary
