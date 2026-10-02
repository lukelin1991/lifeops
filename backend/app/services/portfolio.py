"""
Portfolio math. Pure functions: holdings + prices in, numbers out,
so it is easy to unit test with made-up prices.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.models.invest import Holding
from app.services.market_data import PriceResult

ZERO = Decimal("0")


def _round(value: Decimal, places: str = "0.01") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _percent(part: Decimal, whole: Decimal) -> Decimal | None:
    if whole == 0:
        return None
    return _round(part / whole * 100)


def build_portfolio(
    holdings: list[Holding],
    prices: dict[tuple[str, str], PriceResult],
) -> dict:
    """
    Market value only counts holdings that have a price. Gain/loss is
    measured against the cost basis of those same priced holdings, so a
    missing price never shows up as a fake 100% loss.
    """
    rows = []
    total_cost = ZERO
    priced_cost = ZERO
    market_value = ZERO
    value_by_type: dict[str, Decimal] = {"stock": ZERO, "crypto": ZERO}

    for holding in holdings:
        quantity = Decimal(holding.quantity)
        cost_basis = _round(quantity * Decimal(holding.avg_cost))
        total_cost += cost_basis

        price_info = prices.get((holding.symbol, holding.asset_type))
        price = price_info.price if price_info else None

        row = {
            "id": holding.id,
            "symbol": holding.symbol,
            "asset_type": holding.asset_type,
            "name": holding.name,
            "quantity": quantity,
            "avg_cost": holding.avg_cost,
            "notes": holding.notes,
            "created_at": holding.created_at,
            "price": price,
            "price_status": price_info.price_status if price_info else "unavailable",
            "price_message": price_info.message if price_info else None,
            "cost_basis": cost_basis,
            "market_value": None,
            "gain_loss": None,
            "gain_loss_pct": None,
        }

        if price is not None:
            value = _round(quantity * price)
            gain = value - cost_basis
            row["market_value"] = value
            row["gain_loss"] = gain
            row["gain_loss_pct"] = _percent(gain, cost_basis)

            market_value += value
            priced_cost += cost_basis
            value_by_type[holding.asset_type] = (
                value_by_type.get(holding.asset_type, ZERO) + value
            )

        rows.append(row)

    gain_loss = market_value - priced_cost
    priced_count = sum(1 for r in rows if r["price"] is not None)

    allocation = [
        {
            "asset_type": asset_type,
            "market_value": value,
            "percent": _percent(value, market_value) or ZERO,
        }
        for asset_type, value in value_by_type.items()
    ]

    return {
        "holdings": rows,
        "summary": {
            "market_value": market_value,
            "cost_basis": total_cost,
            "priced_cost_basis": priced_cost,
            "gain_loss": gain_loss,
            "gain_loss_pct": _percent(gain_loss, priced_cost),
            "allocation": allocation,
            "holdings_count": len(rows),
            "priced_count": priced_count,
            "unpriced_count": len(rows) - priced_count,
            "complete": priced_count == len(rows),
        },
    }
