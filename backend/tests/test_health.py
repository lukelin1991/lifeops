"""Luke's original Health endpoints: behaviour must stay exactly the same."""


def add_weight(client, weight, day):
    response = client.post(
        "/weights", json={"weight": weight, "measurement_date": day}
    )
    assert response.status_code == 200
    return response.json()["data"]


def add_goal(client, start, goal):
    response = client.post(
        "/weight-goals",
        json={"starting_weight": start, "goal_weight": goal},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_weight_crud_and_ordering(client):
    created = add_weight(client, 250.5, "2026-09-10")
    assert created["weight"] == 250.5
    assert created["measurement_date"] == "2026-09-10"
    assert "created_at" in created

    add_weight(client, 255, "2026-09-01")

    weights = client.get("/weights").json()["data"]
    # Oldest measurement first
    assert [w["measurement_date"] for w in weights] == ["2026-09-01", "2026-09-10"]

    response = client.patch(f"/weights/{created['id']}", json={"weight": 249})
    assert response.status_code == 200
    assert response.json()["message"] == "Weight updated"
    assert response.json()["data"]["weight"] == 249
    assert response.json()["data"]["measurement_date"] == "2026-09-10"

    response = client.delete(f"/weights/{created['id']}")
    assert response.json() == {"message": "Weight entry deleted"}
    assert len(client.get("/weights").json()["data"]) == 1


def test_weight_not_found(client):
    assert client.patch("/weights/999", json={"weight": 1}).status_code == 404
    response = client.delete("/weights/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Weight entry not found"


def test_goal_must_be_below_start(client):
    response = client.post(
        "/weight-goals", json={"starting_weight": 200, "goal_weight": 210}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Goal weight must be lower than starting weight"


def test_goal_lifecycle(client):
    goal = add_goal(client, 260, 200)
    assert goal["status"] == "planned"

    # Planned goal cannot be completed
    response = client.post(f"/weight-goals/{goal['id']}/complete")
    assert response.status_code == 400

    # No active goal yet
    assert client.get("/weight-goals/active").status_code == 404
    assert client.get("/weight-progress").status_code == 404

    response = client.post(f"/weight-goals/{goal['id']}/activate")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "active"
    assert response.json()["data"]["activated_at"] is not None

    # Already active
    assert client.post(f"/weight-goals/{goal['id']}/activate").status_code == 400

    # Only one active goal at a time
    other = add_goal(client, 250, 220)
    response = client.post(f"/weight-goals/{other['id']}/activate")
    assert response.status_code == 400
    assert response.json()["detail"] == "Another weight goal is already active"

    assert client.get("/weight-goals/active").json()["data"]["id"] == goal["id"]

    # Can't complete without weights
    response = client.post(f"/weight-goals/{goal['id']}/complete")
    assert response.json()["detail"] == "No weight entries found"

    # Can't complete before reaching goal
    add_weight(client, 230, "2026-09-01")
    response = client.post(f"/weight-goals/{goal['id']}/complete")
    assert response.status_code == 400

    add_weight(client, 199.5, "2026-09-20")
    response = client.post(f"/weight-goals/{goal['id']}/complete")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"

    # Completed goals are frozen
    assert client.patch(
        f"/weight-goals/{goal['id']}", json={"goal_weight": 190}
    ).status_code == 400
    assert client.post(f"/weight-goals/{goal['id']}/activate").status_code == 400
    assert client.post(f"/weight-goals/{goal['id']}/complete").status_code == 400


def test_goal_update_validation_and_delete(client):
    goal = add_goal(client, 260, 200)

    response = client.patch(f"/weight-goals/{goal['id']}", json={"goal_weight": 270})
    assert response.status_code == 400

    response = client.patch(f"/weight-goals/{goal['id']}", json={"goal_weight": 210})
    assert response.json()["data"]["goal_weight"] == 210
    assert response.json()["data"]["starting_weight"] == 260

    assert client.get(f"/weight-goals/{goal['id']}").status_code == 200
    assert client.delete(f"/weight-goals/{goal['id']}").json() == {
        "message": "Weight goal deleted"
    }
    assert client.get(f"/weight-goals/{goal['id']}").status_code == 404


def test_goals_listed_newest_first(client):
    first = add_goal(client, 260, 200)
    second = add_goal(client, 250, 210)
    ids = [g["id"] for g in client.get("/weight-goals").json()["data"]]
    assert ids == [second["id"], first["id"]]


def test_weight_progress(client):
    goal = add_goal(client, 260, 200)
    client.post(f"/weight-goals/{goal['id']}/activate")
    add_weight(client, 245, "2026-09-15")

    progress = client.get("/weight-progress").json()
    assert progress["current_weight"] == 245
    assert progress["change_from_start"] == -15
    assert progress["weight_remaining"] == 45
    assert progress["progress_percentage"] == 25
    assert progress["status"] == "progress"
    assert progress["latest_measurement_date"] == "2026-09-15"


def test_weight_progress_statuses(client):
    goal = add_goal(client, 260, 200)
    client.post(f"/weight-goals/{goal['id']}/activate")

    add_weight(client, 265, "2026-09-01")
    progress = client.get("/weight-progress").json()
    assert progress["status"] == "above_start"
    assert progress["progress_percentage"] == 0

    add_weight(client, 260, "2026-09-02")
    assert client.get("/weight-progress").json()["status"] == "starting"

    add_weight(client, 195, "2026-09-03")
    progress = client.get("/weight-progress").json()
    assert progress["status"] == "goal_reached"
    assert progress["progress_percentage"] == 100
    assert progress["weight_remaining"] == 0
