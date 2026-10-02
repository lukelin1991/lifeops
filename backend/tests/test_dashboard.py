def test_dashboard_on_empty_database(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["health"] == {
        "latest_weight": None, "latest_measurement_date": None, "goal_progress": None,
    }
    assert data["money"]["spending"] == 0
    assert data["calendar"]["events"] == []
    assert data["invest"]["status"] == "ok"
    assert data["invest"]["summary"]["market_value"] == 0
    assert data["career"]["total"] == 0


def test_dashboard_with_data(client, market):
    from app.services.dates import today

    current = today()

    client.post("/weights", json={"weight": 250, "measurement_date": current.isoformat()})
    goal = client.post("/weight-goals", json={"starting_weight": 260, "goal_weight": 200}).json()
    client.post(f"/weight-goals/{goal['data']['id']}/activate")

    food = client.post("/money/categories", json={"name": "Food"}).json()["data"]
    client.post("/money/budgets", json={
        "category_id": food["id"], "year": current.year, "month": current.month, "amount": "50",
    })
    client.post("/money/transactions", json={
        "transaction_type": "expense", "amount": "80", "category_id": food["id"],
        "transaction_date": current.isoformat(),
    })
    client.post("/money/bills", json={
        "name": "Phone", "amount": "45", "due_day": current.day,
        "start_date": current.isoformat(),
    })

    client.post("/calendar/events", json={
        "title": "Gym", "start_at": f"{current}T18:00:00",
    })
    client.post("/calendar/tasks", json={"title": "Ship LifeOps", "due_date": current.isoformat()})

    client.post("/invest/holdings", json={
        "symbol": "AAPL", "asset_type": "stock", "quantity": "10", "avg_cost": "100",
    })
    client.post("/invest/holdings", json={
        "symbol": "BTC", "asset_type": "crypto", "quantity": "1", "avg_cost": "100",
    })
    market.set_price("AAPL", "stock", 110)

    client.post("/career/applications", json={"company": "Acme", "title": "SRE"})

    data = client.get("/dashboard").json()

    assert data["health"]["latest_weight"] == 250
    assert data["health"]["goal_progress"]["progress_percentage"] == 16.7

    assert data["money"]["spending"] == 80
    assert data["money"]["budget_remaining"] == -30
    assert data["money"]["over_budget_categories"][0]["category_name"] == "Food"
    assert data["money"]["upcoming_bills"][0]["name"] == "Phone"

    assert [e["title"] for e in data["calendar"]["events"]] == ["Gym"]
    assert [t["title"] for t in data["calendar"]["tasks"]] == ["Ship LifeOps"]

    assert data["invest"]["status"] == "partial"  # BTC has no price
    assert data["invest"]["summary"]["market_value"] == 1100

    assert data["career"]["counts"]["applied"] == 1


def test_dashboard_survives_market_data_crash(client, market):
    client.post("/invest/holdings", json={
        "symbol": "AAPL", "asset_type": "stock", "quantity": "1", "avg_cost": "1",
    })
    market.fail = True

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json()["invest"] == {"status": "unavailable", "summary": None}
