from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.invest import Holding, WatchlistItem
from app.schemas.invest import (
    HoldingCreate,
    HoldingRead,
    HoldingUpdate,
    Portfolio,
    Quote,
    WatchlistCreate,
    WatchlistRead,
    WatchlistUpdate,
    WatchlistWithPrice,
)
from app.services.crud import apply_update, get_or_404
from app.services.market_data import MarketDataService, get_market_data
from app.services.portfolio import build_portfolio

router = APIRouter(
    prefix="/invest",
    tags=["Invest"]
)


def _commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail)


# ---------------------------------------------------------
# HOLDINGS
# ---------------------------------------------------------

@router.get("/holdings")
def list_holdings(db: Session = Depends(get_db)):
    """Stored holdings only (no prices, no network calls)."""
    holdings = db.scalars(
        select(Holding).order_by(Holding.asset_type, Holding.symbol)
    ).all()
    return {"data": [HoldingRead.model_validate(h) for h in holdings]}


@router.post("/holdings", status_code=201)
def create_holding(holding: HoldingCreate, db: Session = Depends(get_db)):
    item = Holding(**holding.model_dump())
    db.add(item)
    _commit_or_conflict(db, "You already hold this symbol; edit it instead")
    db.refresh(item)
    return {"message": "Holding added", "data": HoldingRead.model_validate(item)}


@router.get("/holdings/{holding_id}")
def get_holding(holding_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Holding, holding_id, "Holding")
    return {"data": HoldingRead.model_validate(item)}


@router.patch("/holdings/{holding_id}")
def update_holding(
    holding_id: int,
    holding: HoldingUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Holding, holding_id, "Holding")
    apply_update(item, holding)
    db.commit()
    db.refresh(item)
    return {"message": "Holding updated", "data": HoldingRead.model_validate(item)}


@router.delete("/holdings/{holding_id}")
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Holding, holding_id, "Holding")
    db.delete(item)
    db.commit()
    return {"message": "Holding deleted"}


# ---------------------------------------------------------
# PORTFOLIO (holdings + live prices)
# ---------------------------------------------------------

@router.get("/portfolio", response_model=Portfolio)
def get_portfolio(
    db: Session = Depends(get_db),
    market: MarketDataService = Depends(get_market_data),
):
    holdings = db.scalars(
        select(Holding).order_by(Holding.asset_type, Holding.symbol)
    ).all()

    prices = market.get_prices([(h.symbol, h.asset_type) for h in holdings])
    return build_portfolio(holdings, prices)


@router.get("/quote/{asset_type}/{symbol}", response_model=Quote)
def get_quote(
    asset_type: Literal["stock", "crypto"],
    symbol: str,
    market: MarketDataService = Depends(get_market_data),
):
    result = market.get_price(symbol, asset_type)
    return Quote(
        symbol=result.symbol,
        asset_type=result.asset_type,
        price=result.price,
        price_status=result.price_status,
        source=result.source,
        message=result.message,
    )


# ---------------------------------------------------------
# WATCHLIST
# ---------------------------------------------------------

@router.get("/watchlist")
def list_watchlist(
    with_prices: bool = False,
    db: Session = Depends(get_db),
    market: MarketDataService = Depends(get_market_data),
):
    items = db.scalars(
        select(WatchlistItem).order_by(WatchlistItem.symbol)
    ).all()

    if not with_prices:
        return {"data": [WatchlistRead.model_validate(i) for i in items]}

    prices = market.get_prices([(i.symbol, i.asset_type) for i in items])
    data = []

    for item in items:
        price_info = prices[(item.symbol, item.asset_type)]
        below_target = None
        if price_info.price is not None and item.target_price is not None:
            below_target = price_info.price <= item.target_price

        data.append(
            WatchlistWithPrice(
                **WatchlistRead.model_validate(item).model_dump(),
                price=price_info.price,
                price_status=price_info.price_status,
                price_message=price_info.message,
                below_target=below_target,
            )
        )

    return {"data": data}


@router.post("/watchlist", status_code=201)
def create_watchlist_item(
    item_in: WatchlistCreate,
    db: Session = Depends(get_db),
):
    item = WatchlistItem(**item_in.model_dump())
    db.add(item)
    _commit_or_conflict(db, "This symbol is already on your watchlist")
    db.refresh(item)
    return {"message": "Added to watchlist", "data": WatchlistRead.model_validate(item)}


@router.patch("/watchlist/{item_id}")
def update_watchlist_item(
    item_id: int,
    item_in: WatchlistUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, WatchlistItem, item_id, "Watchlist item")
    apply_update(item, item_in)
    db.commit()
    db.refresh(item)
    return {"message": "Watchlist item updated", "data": WatchlistRead.model_validate(item)}


@router.delete("/watchlist/{item_id}")
def delete_watchlist_item(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, WatchlistItem, item_id, "Watchlist item")
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}
