import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.services import money as money_service
from app.services.dates import today


def make_category(client, name, kind="expense"):
    response = client.post("/money/categories", json={"name": name, "kind": kind})
    assert response.status_code == 201, response.text
    return response.json()["data"]


def make_tx(client, **values):
    payload = {
        "transaction_type": "expense",
        "amount": "10.00",
        "transaction_date": "2026-09-15",
    }
    payload.update(values)
    response = client.post("/money/transactions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


# ---------------------------------------------------------
# CRUD
# ---------------------------------------------------------

def test_accounts_crud(client):
    response = client.post(
        "/money/accounts",
        json={"name": "Checking", "account_type": "checking", "balance": "1520.55"},
    )
    assert response.status_code == 201
    account = response.json()["data"]
    assert account["balance"] == 1520.55  # JSON number, not a string

    response = client.patch(f"/money/accounts/{account['id']}", json={"balance": "99.10"})
    assert response.json()["data"]["balance"] == 99.1

    assert len(client.get("/money/accounts").json()["data"]) == 1
    assert client.delete(f"/money/accounts/{account['id']}").status_code == 200
    assert client.delete(f"/money/accounts/{account['id']}").status_code == 404


def test_categories_crud_and_unique_name(client):
    groceries = make_category(client, "Groceries")
    make_category(client, "Salary", "income")

    response = client.post("/money/categories", json={"name": "Groceries"})
    assert response.status_code == 409

    response = client.patch(
        f"/money/categories/{groceries['id']}", json={"name": "Food"}
    )
    assert response.json()["data"]["name"] == "Food"

    names = [c["name"] for c in client.get("/money/categories").json()["data"]]
    assert names == ["Food", "Salary"]

    assert client.delete(f"/money/categories/{groceries['id']}").status_code == 200


def test_transactions_crud_and_filters(client):
    food = make_category(client, "Food")
    rent = make_category(client, "Rent")

    tx = make_tx(
        client, amount="45.67", merchant="Trader Joe's",
        category_id=food["id"], transaction_date="2026-09-03",
    )
    assert tx["amount"] == 45.67
    assert tx["category_name"] == "Food"

    make_tx(client, amount="1800", category_id=rent["id"], transaction_date="2026-09-01")
    make_tx(client, transaction_type="income", amount="4000", transaction_date="2026-09-15")
    make_tx(client, amount="20", category_id=food["id"], transaction_date="2026-08-30")

    all_tx = client.get("/money/transactions").json()["data"]
    assert len(all_tx) == 4
    assert all_tx[0]["transaction_date"] == "2026-09-15"  # newest first

    september = client.get(
        "/money/transactions",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
    ).json()["data"]
    assert len(september) == 3

    food_only = client.get(
        "/money/transactions", params={"category_id": food["id"]}
    ).json()["data"]
    assert {t["amount"] for t in food_only} == {45.67, 20}

    income = client.get(
        "/money/transactions", params={"transaction_type": "income"}
    ).json()["data"]
    assert len(income) == 1

    response = client.get(
        "/money/transactions",
        params={"start_date": "2026-09-30", "end_date": "2026-09-01"},
    )
    assert response.status_code == 400

    # Update, clear the category, delete
    response = client.patch(
        f"/money/transactions/{tx['id']}",
        json={"amount": "50.00", "category_id": None, "notes": "split w/ friend"},
    )
    data = response.json()["data"]
    assert data["amount"] == 50
    assert data["category_id"] is None
    assert data["notes"] == "split w/ friend"

    assert client.get(f"/money/transactions/{tx['id']}").status_code == 200
    assert client.delete(f"/money/transactions/{tx['id']}").status_code == 200
    assert client.get(f"/money/transactions/{tx['id']}").status_code == 404


def test_transaction_validation(client):
    response = client.post(
        "/money/transactions",
        json={"transaction_type": "expense", "amount": "-5", "transaction_date": "2026-09-01"},
    )
    assert response.status_code == 422

    response = client.post(
        "/money/transactions",
        json={"transaction_type": "gift", "amount": "5", "transaction_date": "2026-09-01"},
    )
    assert response.status_code == 422

    response = client.post(
        "/money/transactions",
        json={"transaction_type": "expense", "amount": "5",
              "transaction_date": "2026-09-01", "category_id": 999},
    )
    assert response.status_code == 400


def test_deleting_category_keeps_transactions(client):
    food = make_category(client, "Food")
    tx = make_tx(client, category_id=food["id"])
    client.delete(f"/money/categories/{food['id']}")
    data = client.get(f"/money/transactions/{tx['id']}").json()["data"]
    assert data["category_id"] is None


def test_budgets_crud_unique_and_copy(client):
    food = make_category(client, "Food")
    fun = make_category(client, "Fun")

    response = client.post(
        "/money/budgets",
        json={"category_id": food["id"], "year": 2026, "month": 9, "amount": "600"},
    )
    assert response.status_code == 201
    budget = response.json()["data"]
    assert budget["category_name"] == "Food"

    response = client.post(
        "/money/budgets",
        json={"category_id": food["id"], "year": 2026, "month": 9, "amount": "700"},
    )
    assert response.status_code == 409

    client.post(
        "/money/budgets",
        json={"category_id": fun["id"], "year": 2026, "month": 9, "amount": "150"},
    )

    response = client.patch(f"/money/budgets/{budget['id']}", json={"amount": "650"})
    assert response.json()["data"]["amount"] == 650

    response = client.post(
        "/money/budgets/copy", params={"from_year": 2026, "from_month": 9}
    )
    assert response.status_code == 201
    assert len(response.json()["data"]) == 2

    october = client.get("/money/budgets", params={"year": 2026, "month": 10}).json()["data"]
    assert {b["amount"] for b in october} == {650, 150}

    # Copying again doesn't duplicate
    response = client.post(
        "/money/budgets/copy", params={"from_year": 2026, "from_month": 9}
    )
    assert response.json()["data"] == []

    assert client.delete(f"/money/budgets/{budget['id']}").status_code == 200


def test_bills_crud_with_next_due(client):
    response = client.post(
        "/money/bills",
        json={"name": "Internet", "amount": "79.99", "due_day": 15, "autopay": True},
    )
    assert response.status_code == 201
    bill = response.json()["data"]
    assert bill["start_date"] == today().isoformat()
    assert bill["next_due_date"] is not None
    assert datetime.date.fromisoformat(bill["next_due_date"]) >= today()

    response = client.patch(f"/money/bills/{bill['id']}", json={"is_active": False})
    assert response.json()["data"]["next_due_date"] is None

    assert len(client.get("/money/bills").json()["data"]) == 1
    assert client.get(f"/money/bills/{bill['id']}").status_code == 200
    assert client.delete(f"/money/bills/{bill['id']}").status_code == 200


def test_debts_crud(client):
    response = client.post(
        "/money/debts",
        json={"name": "Visa", "balance": "3200.50", "apr": "24.99", "minimum_payment": "95"},
    )
    assert response.status_code == 201
    debt = response.json()["data"]
    assert debt["apr"] == 24.99

    response = client.patch(f"/money/debts/{debt['id']}", json={"balance": "3000"})
    assert response.json()["data"]["balance"] == 3000

    assert client.get(f"/money/debts/{debt['id']}").status_code == 200
    assert len(client.get("/money/debts").json()["data"]) == 1
    assert client.delete(f"/money/debts/{debt['id']}").status_code == 200


# ---------------------------------------------------------
# BILL SCHEDULE MATH
# ---------------------------------------------------------

def bill(**values):
    defaults = {
        "id": 1, "name": "Bill", "amount": Decimal("10"), "due_day": 15,
        "frequency": "monthly", "start_date": datetime.date(2026, 1, 1),
        "autopay": False, "is_active": True,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_monthly_bill_next_due():
    b = bill(due_day=15)
    assert money_service.next_due_date(b, datetime.date(2026, 9, 10)) == datetime.date(2026, 9, 15)
    assert money_service.next_due_date(b, datetime.date(2026, 9, 15)) == datetime.date(2026, 9, 15)
    assert money_service.next_due_date(b, datetime.date(2026, 9, 16)) == datetime.date(2026, 10, 15)


def test_due_day_31_is_clamped_to_month_end():
    b = bill(due_day=31)
    dates = money_service.bill_due_dates(
        b, datetime.date(2027, 1, 1), datetime.date(2027, 4, 30)
    )
    assert dates == [
        datetime.date(2027, 1, 31),
        datetime.date(2027, 2, 28),
        datetime.date(2027, 3, 31),
        datetime.date(2027, 4, 30),
    ]


def test_quarterly_and_yearly_bills_follow_start_month():
    quarterly = bill(frequency="quarterly", start_date=datetime.date(2026, 2, 1), due_day=1)
    assert money_service.next_due_date(
        quarterly, datetime.date(2026, 9, 2)
    ) == datetime.date(2026, 11, 1)

    yearly = bill(frequency="yearly", start_date=datetime.date(2024, 3, 20), due_day=20)
    assert money_service.next_due_date(
        yearly, datetime.date(2026, 9, 1)
    ) == datetime.date(2027, 3, 20)


def test_bill_not_due_before_its_start_date():
    b = bill(start_date=datetime.date(2026, 9, 20), due_day=10)
    assert money_service.next_due_date(b, datetime.date(2026, 9, 1)) == datetime.date(2026, 10, 10)


# ---------------------------------------------------------
# DEBT PAYOFF MATH
# ---------------------------------------------------------

def debt(debt_id, balance, apr, minimum, name=None):
    return SimpleNamespace(
        id=debt_id, name=name or f"Debt {debt_id}",
        balance=Decimal(balance), apr=Decimal(apr), minimum_payment=Decimal(minimum),
    )


def test_zero_interest_debt_is_simple_division():
    plan = money_service.project_debt_payoff([debt(1, "1200", "0", "100")])
    assert plan.feasible
    assert plan.months_to_payoff == 12
    assert plan.total_interest == 0
    assert plan.total_paid == Decimal("1200")


def test_single_debt_matches_amortization_formula():
    # $1,000 at 12% APR paying $100/month: the closed-form formula gives
    # n = -ln(1 - 0.01 * 1000 / 100) / ln(1.01) = 10.59 -> 11 payments
    plan = money_service.project_debt_payoff([debt(1, "1000", "12", "100")])
    assert plan.months_to_payoff == 11
    # Interest: month 1 is $10.00, total about $58
    assert Decimal("55") < plan.total_interest < Decimal("60")
    assert plan.total_paid == Decimal("1000") + plan.total_interest


def test_avalanche_orders_by_apr_and_extra_payment_helps():
    debts = [
        debt(1, "5000", "6.5", "100", "Car"),
        debt(2, "2000", "24.99", "60", "Visa"),
        debt(3, "800", "18", "30", "Store card"),
    ]

    baseline = money_service.project_debt_payoff(debts, Decimal("0"))
    plan = money_service.project_debt_payoff(debts, Decimal("300"))

    assert [d["name"] for d in plan.debts] == ["Visa", "Store card", "Car"]
    assert plan.feasible and baseline.feasible
    assert plan.monthly_payment == Decimal("490")
    assert plan.months_to_payoff < baseline.months_to_payoff
    assert plan.total_interest < baseline.total_interest

    # Highest-APR debt is paid off first
    payoff = {d["name"]: d["months_to_payoff"] for d in plan.debts}
    assert payoff["Visa"] <= payoff["Store card"] <= payoff["Car"]


def test_snowball_orders_by_balance():
    debts = [debt(1, "5000", "6.5", "100", "Car"), debt(2, "800", "3", "30", "Small")]
    plan = money_service.project_debt_payoff(debts, Decimal("100"), strategy="snowball")
    assert [d["name"] for d in plan.debts] == ["Small", "Car"]


def test_payments_below_interest_are_flagged_infeasible():
    plan = money_service.project_debt_payoff([debt(1, "10000", "30", "100")])
    # Interest is $250/month but only $100 is paid
    assert not plan.feasible
    assert plan.months_to_payoff is None


def test_payoff_endpoint(client):
    client.post("/money/debts", json={"name": "Visa", "balance": "2000", "apr": "24.99",
                                      "minimum_payment": "60"})
    client.post("/money/debts", json={"name": "Car", "balance": "5000", "apr": "6.5",
                                      "minimum_payment": "150"})

    result = client.get("/money/debts/payoff", params={"extra_payment": "200"}).json()
    assert result["strategy"] == "avalanche"
    assert result["feasible"] is True
    assert result["monthly_payment"] == 410
    assert result["debts"][0]["name"] == "Visa"
    assert result["months_to_payoff"] < result["baseline_months"]
    assert result["interest_saved"] > 0
    assert len(result["payoff_month"]) == 7  # "YYYY-MM"

    empty_extra = client.get("/money/debts/payoff").json()
    assert empty_extra["interest_saved"] == 0


def test_payoff_endpoint_with_no_debts(client):
    result = client.get("/money/debts/payoff").json()
    assert result["feasible"] is True
    assert result["months_to_payoff"] == 0
    assert result["total_interest"] == 0


# ---------------------------------------------------------
# MONTHLY SUMMARY
# ---------------------------------------------------------

def test_monthly_summary_vs_budget(client):
    food = make_category(client, "Food")
    fun = make_category(client, "Fun")
    make_category(client, "Travel")

    for category, amount in [(food, "300"), (fun, "100")]:
        client.post("/money/budgets", json={
            "category_id": category["id"], "year": 2026, "month": 9, "amount": amount,
        })

    make_tx(client, amount="120.50", category_id=food["id"], transaction_date="2026-09-02")
    make_tx(client, amount="99.50", category_id=food["id"], transaction_date="2026-09-20")
    make_tx(client, amount="130", category_id=fun["id"], transaction_date="2026-09-21")
    make_tx(client, amount="40", transaction_date="2026-09-22")  # uncategorized
    make_tx(client, transaction_type="income", amount="5000", transaction_date="2026-09-30")
    make_tx(client, amount="999", category_id=food["id"], transaction_date="2026-10-01")

    summary = client.get("/money/summary", params={"year": 2026, "month": 9}).json()

    assert summary["income"] == 5000
    assert summary["spending"] == 390
    assert summary["net"] == 4610
    assert summary["total_budget"] == 400
    assert summary["budget_remaining"] == 10

    rows = {row["category_name"]: row for row in summary["by_category"]}
    assert rows["Food"]["spent"] == 220
    assert rows["Food"]["remaining"] == 80
    assert rows["Food"]["over_budget"] is False
    assert rows["Fun"]["over_budget"] is True
    assert rows["Fun"]["remaining"] == -30
    assert rows["Uncategorized"]["budget"] is None
    assert "Travel" not in rows  # no spending and no budget


def test_summary_upcoming_bills_before_date(client):
    current = today()
    # Due today (counts) and a yearly bill far in the future (doesn't)
    client.post("/money/bills", json={
        "name": "Phone", "amount": "45", "due_day": current.day, "start_date": current.isoformat(),
    })
    client.post("/money/bills", json={
        "name": "Domain", "amount": "15", "due_day": 1, "frequency": "yearly",
        "start_date": (current + datetime.timedelta(days=120)).isoformat(),
    })

    summary = client.get("/money/summary").json()
    names = [b["name"] for b in summary["upcoming_bills"]]
    assert names == ["Phone"]
    assert summary["upcoming_bills"][0]["due_date"] == current.isoformat()
    assert summary["upcoming_bills_total"] == 45

    # Exclusive: nothing is due before today
    summary = client.get("/money/summary", params={"bills_before": current.isoformat()}).json()
    assert summary["upcoming_bills"] == []


def test_upcoming_bills_service_lists_each_occurrence(db_session):
    from app.models.money import RecurringBill

    db_session.add(RecurringBill(
        name="Gym", amount=Decimal("30"), due_day=5, frequency="monthly",
        start_date=datetime.date(2026, 1, 1),
    ))
    db_session.commit()

    bills = money_service.upcoming_bills(
        db_session, datetime.date(2026, 9, 1), datetime.date(2026, 12, 1)
    )
    assert [b["due_date"] for b in bills] == [
        datetime.date(2026, 9, 5), datetime.date(2026, 10, 5), datetime.date(2026, 11, 5),
    ]
