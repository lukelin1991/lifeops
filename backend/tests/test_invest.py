from decimal import Decimal

import httpx
import pytest

from app.services.market_data import MarketDataService, PriceResult
from app.services.portfolio import build_portfolio


def add_holding(client, symbol, asset_type, quantity, avg_cost):
    response = client.post("/invest/holdings", json={
        "symbol": symbol, "asset_type": asset_type,
        "quantity": str(quantity), "avg_cost": str(avg_cost),
    })
    assert response.status_code == 201, response.text
    return response.json()["data"]


# ---------------------------------------------------------
# HOLDINGS / WATCHLIST CRUD
# ---------------------------------------------------------

def test_holdings_crud(client):
    holding = add_holding(client, " aapl ", "stock", 10, "150.25")
    assert holding["symbol"] == "AAPL"
    assert holding["quantity"] == 10
    assert holding["avg_cost"] == 150.25

    response = client.post("/invest/holdings", json={
        "symbol": "AAPL", "asset_type": "stock", "quantity": "1", "avg_cost": "1",
    })
    assert response.status_code == 409

    # Same ticker as a different asset type is allowed
    add_holding(client, "AAPL", "crypto", 1, 1)

    response = client.patch(f"/invest/holdings/{holding['id']}", json={"quantity": "12.5"})
    assert response.json()["data"]["quantity"] == 12.5

    assert len(client.get("/invest/holdings").json()["data"]) == 2
    assert client.get(f"/invest/holdings/{holding['id']}").status_code == 200
    assert client.delete(f"/invest/holdings/{holding['id']}").status_code == 200
    assert client.get(f"/invest/holdings/{holding['id']}").status_code == 404


def test_holding_validation(client):
    bad = [
        {"symbol": "X", "asset_type": "bond", "quantity": "1", "avg_cost": "1"},
        {"symbol": "X", "asset_type": "stock", "quantity": "0", "avg_cost": "1"},
        {"symbol": "   ", "asset_type": "stock", "quantity": "1", "avg_cost": "1"},
    ]
    for payload in bad:
        assert client.post("/invest/holdings", json=payload).status_code == 422


def test_watchlist_crud_and_prices(client, market):
    response = client.post("/invest/watchlist", json={
        "symbol": "nvda", "asset_type": "stock", "target_price": "100",
    })
    assert response.status_code == 201
    item = response.json()["data"]
    assert item["symbol"] == "NVDA"

    assert client.post("/invest/watchlist", json={
        "symbol": "NVDA", "asset_type": "stock",
    }).status_code == 409

    client.post("/invest/watchlist", json={"symbol": "SOL", "asset_type": "crypto"})
    market.set_price("NVDA", "stock", "95.5")

    plain = client.get("/invest/watchlist").json()["data"]
    assert "price" not in plain[0]
    assert market.calls == 0  # no market call unless asked

    priced = {i["symbol"]: i for i in client.get(
        "/invest/watchlist", params={"with_prices": True}
    ).json()["data"]}
    assert priced["NVDA"]["price"] == 95.5
    assert priced["NVDA"]["below_target"] is True
    assert priced["SOL"]["price"] is None
    assert priced["SOL"]["price_status"] == "missing_api_key"

    response = client.patch(f"/invest/watchlist/{item['id']}", json={"target_price": "90"})
    assert response.json()["data"]["target_price"] == 90
    assert client.delete(f"/invest/watchlist/{item['id']}").status_code == 200


# ---------------------------------------------------------
# PORTFOLIO MATH (mocked prices)
# ---------------------------------------------------------

def test_portfolio_with_all_prices(client, market):
    add_holding(client, "AAPL", "stock", 10, 100)     # cost 1,000
    add_holding(client, "MSFT", "stock", 2, 300)      # cost   600
    add_holding(client, "BTC", "crypto", "0.5", 20000)  # cost 10,000

    market.set_price("AAPL", "stock", 150)    # value 1,500 (+500)
    market.set_price("MSFT", "stock", 250)    # value   500 (-100)
    market.set_price("BTC", "crypto", 60000)  # value 30,000 (+20,000)

    portfolio = client.get("/invest/portfolio").json()
    summary = portfolio["summary"]

    assert summary["market_value"] == 32000
    assert summary["cost_basis"] == 11600
    assert summary["gain_loss"] == 20400
    assert summary["gain_loss_pct"] == 175.86
    assert summary["complete"] is True

    allocation = {a["asset_type"]: a for a in summary["allocation"]}
    assert allocation["stock"]["market_value"] == 2000
    assert allocation["stock"]["percent"] == 6.25
    assert allocation["crypto"]["percent"] == 93.75

    rows = {h["symbol"]: h for h in portfolio["holdings"]}
    assert rows["MSFT"]["gain_loss"] == -100
    assert rows["MSFT"]["gain_loss_pct"] == -16.67
    assert rows["AAPL"]["price_status"] == "ok"


def test_portfolio_tolerates_missing_prices(client, market):
    add_holding(client, "AAPL", "stock", 10, 100)
    add_holding(client, "ETH", "crypto", 2, 1500)
    market.set_price("AAPL", "stock", 120)

    portfolio = client.get("/invest/portfolio").json()
    summary = portfolio["summary"]
    rows = {h["symbol"]: h for h in portfolio["holdings"]}

    assert rows["ETH"]["price"] is None
    assert rows["ETH"]["market_value"] is None
    assert rows["ETH"]["price_status"] == "missing_api_key"
    assert rows["ETH"]["cost_basis"] == 3000

    # Only priced holdings count toward value and gain/loss
    assert summary["market_value"] == 1200
    assert summary["cost_basis"] == 4000
    assert summary["priced_cost_basis"] == 1000
    assert summary["gain_loss"] == 200
    assert summary["gain_loss_pct"] == 20
    assert summary["complete"] is False
    assert summary["unpriced_count"] == 1


def test_empty_portfolio(client):
    summary = client.get("/invest/portfolio").json()["summary"]
    assert summary["market_value"] == 0
    assert summary["gain_loss_pct"] is None
    assert summary["complete"] is True


def test_quote_endpoint(client, market):
    market.set_price("AAPL", "stock", "201.5")
    quote = client.get("/invest/quote/stock/aapl").json()
    assert quote == {
        "symbol": "AAPL", "asset_type": "stock", "price": 201.5,
        "price_status": "ok", "source": "fake", "message": None,
    }
    assert client.get("/invest/quote/bond/X").status_code == 422


def test_build_portfolio_is_pure():
    from types import SimpleNamespace

    holding = SimpleNamespace(
        id=1, symbol="TSLA", asset_type="stock", name=None, quantity=Decimal("3"),
        avg_cost=Decimal("200"), notes=None, created_at=None,
    )
    prices = {("TSLA", "stock"): PriceResult("TSLA", "stock", Decimal("250"), "ok")}
    result = build_portfolio([holding], prices)
    assert result["summary"]["market_value"] == Decimal("750.00")
    assert result["summary"]["gain_loss"] == Decimal("150.00")
    assert result["summary"]["gain_loss_pct"] == Decimal("25.00")


# ---------------------------------------------------------
# MARKET DATA CLIENT (httpx.MockTransport, no network)
# ---------------------------------------------------------

def make_service(handler, twelve="td-key", gecko="cg-key", ttl=60):
    calls = []

    def recording_handler(request):
        calls.append(request)
        return handler(request)

    service = MarketDataService(
        twelve_data_api_key=twelve,
        coingecko_api_key=gecko,
        cache_ttl_seconds=ttl,
        transport=httpx.MockTransport(recording_handler),
    )
    return service, calls


def test_missing_keys_never_call_out():
    service, calls = make_service(lambda r: httpx.Response(500), twelve="", gecko="")
    prices = service.get_prices([("AAPL", "stock"), ("BTC", "crypto")])
    assert prices[("AAPL", "stock")].price_status == "missing_api_key"
    assert prices[("BTC", "crypto")].price_status == "missing_api_key"
    assert prices[("AAPL", "stock")].price is None
    assert calls == []


def test_twelve_data_single_symbol_and_cache():
    def handler(request):
        assert request.url.host == "api.twelvedata.com"
        assert request.url.path == "/price"
        assert request.url.params["symbol"] == "AAPL"
        assert request.headers["Authorization"] == "apikey td-key"
        return httpx.Response(200, json={"price": "200.99001"})

    service, calls = make_service(handler)
    result = service.get_price("aapl", "stock")
    assert result.price == Decimal("200.99001")
    assert result.price_status == "ok"
    assert result.source == "twelvedata"

    service.get_price("AAPL", "stock")
    assert len(calls) == 1  # second call served from the 60s cache


def test_twelve_data_batch_with_one_bad_symbol():
    def handler(request):
        assert request.url.params["symbol"] == "AAPL,MSFT,ZZZZ"
        return httpx.Response(200, json={
            "AAPL": {"price": "200.1"},
            "MSFT": {"price": "410.5"},
            "ZZZZ": {"code": 404, "message": "symbol not found", "status": "error"},
        })

    service, _ = make_service(handler)
    prices = service.get_prices([("MSFT", "stock"), ("AAPL", "stock"), ("ZZZZ", "stock")])
    assert prices[("AAPL", "stock")].price == Decimal("200.1")
    assert prices[("MSFT", "stock")].price == Decimal("410.5")
    assert prices[("ZZZZ", "stock")].price_status == "not_found"


def test_twelve_data_rate_limit_is_unavailable():
    service, _ = make_service(lambda r: httpx.Response(200, json={
        "code": 429, "message": "You have run out of API credits", "status": "error",
    }))
    result = service.get_price("AAPL", "stock")
    assert result.price is None
    assert result.price_status == "unavailable"


def test_twelve_data_http_error_keeps_provider_message():
    service, _ = make_service(lambda r: httpx.Response(401, json={
        "code": 401, "message": "Invalid API key", "status": "error",
    }))
    result = service.get_price("AAPL", "stock")
    assert result.price_status == "unavailable"
    assert result.message == "Invalid API key"


@pytest.mark.parametrize("failure", ["timeout", "500", "bad-json"])
def test_network_failures_become_unavailable(failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ConnectTimeout("timed out", request=request)
        if failure == "500":
            return httpx.Response(500, text="oops")
        return httpx.Response(200, text="<html>not json</html>")

    service, _ = make_service(handler)
    prices = service.get_prices([("AAPL", "stock"), ("BTC", "crypto")])
    assert prices[("AAPL", "stock")].price_status == "unavailable"
    assert prices[("BTC", "crypto")].price_status == "unavailable"


def test_coingecko_known_symbols_use_lookup_table():
    def handler(request):
        assert request.url.host == "api.coingecko.com"
        assert request.url.path == "/api/v3/simple/price"
        assert request.headers["x-cg-demo-api-key"] == "cg-key"
        assert request.url.params["ids"] == "bitcoin,ethereum"
        assert request.url.params["vs_currencies"] == "usd"
        return httpx.Response(200, json={
            "bitcoin": {"usd": 64250.12}, "ethereum": {"usd": 3100.5},
        })

    service, calls = make_service(handler)
    prices = service.get_prices([("BTC", "crypto"), ("eth", "crypto")])
    assert prices[("BTC", "crypto")].price == Decimal("64250.12")
    assert prices[("ETH", "crypto")].price == Decimal("3100.5")
    assert len(calls) == 1


def test_coingecko_search_fallback_for_unknown_symbol():
    def handler(request):
        if request.url.path == "/api/v3/search":
            assert request.url.params["query"] == "PEPE"
            return httpx.Response(200, json={"coins": [
                {"id": "pepe-imposter", "symbol": "PEPEX"},
                {"id": "pepe", "symbol": "pepe"},
            ]})
        assert request.url.params["ids"] == "pepe"
        return httpx.Response(200, json={"pepe": {"usd": 0.0000123}})

    service, calls = make_service(handler)
    assert service.get_price("PEPE", "crypto").price == Decimal("0.0000123")
    assert len(calls) == 2

    # Both the id and the price are cached now
    service.get_price("PEPE", "crypto")
    assert len(calls) == 2


def test_coingecko_unknown_symbol_is_not_found():
    def handler(request):
        if request.url.path == "/api/v3/search":
            return httpx.Response(200, json={"coins": []})
        raise AssertionError("price endpoint should not be called")

    service, _ = make_service(handler)
    result = service.get_price("NOPE", "crypto")
    assert result.price_status == "not_found"
    assert result.price is None


def test_expired_cache_fetches_again():
    service, calls = make_service(
        lambda r: httpx.Response(200, json={"price": "1"}), ttl=0
    )
    service.get_price("AAPL", "stock")
    service.get_price("AAPL", "stock")
    assert len(calls) == 2
