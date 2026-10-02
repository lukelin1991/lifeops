import datetime

from app.services.calendar import next_occurrence
from app.services.dates import today


def make_event(client, **values):
    payload = {"title": "Standup", "start_at": "2026-10-05T09:00:00",
               "end_at": "2026-10-05T09:15:00"}
    payload.update(values)
    response = client.post("/calendar/events", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def make_task(client, **values):
    payload = {"title": "Do the thing"}
    payload.update(values)
    response = client.post("/calendar/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_events_crud(client):
    event = make_event(client, location="Zoom")
    assert event["all_day"] is False
    assert event["location"] == "Zoom"

    response = client.patch(f"/calendar/events/{event['id']}", json={"title": "Daily standup"})
    assert response.json()["data"]["title"] == "Daily standup"

    assert client.get(f"/calendar/events/{event['id']}").status_code == 200
    assert len(client.get("/calendar/events").json()["data"]) == 1
    assert client.delete(f"/calendar/events/{event['id']}").status_code == 200
    assert client.get(f"/calendar/events/{event['id']}").status_code == 404


def test_event_end_must_be_after_start(client):
    response = client.post("/calendar/events", json={
        "title": "Bad", "start_at": "2026-10-05T10:00:00", "end_at": "2026-10-05T09:00:00",
    })
    assert response.status_code == 422

    event = make_event(client)
    response = client.patch(
        f"/calendar/events/{event['id']}", json={"end_at": "2026-10-04T09:00:00"}
    )
    assert response.status_code == 400


def test_events_range_filter_includes_multi_day_events(client):
    make_event(client, title="Conference", start_at="2026-10-04T08:00:00",
               end_at="2026-10-06T17:00:00")
    make_event(client, title="Later", start_at="2026-10-20T08:00:00", end_at=None)

    events = client.get("/calendar/events", params={
        "start_date": "2026-10-05", "end_date": "2026-10-05",
    }).json()["data"]
    assert [e["title"] for e in events] == ["Conference"]


def test_tasks_crud(client):
    task = make_task(client, due_date="2026-10-03", priority="high")
    assert task["status"] == "todo"
    assert task["recurrence"] == "none"

    response = client.patch(f"/calendar/tasks/{task['id']}", json={"status": "done"})
    assert response.json()["data"]["completed_at"] is not None

    response = client.patch(f"/calendar/tasks/{task['id']}", json={"status": "todo"})
    assert response.json()["data"]["completed_at"] is None

    open_tasks = client.get("/calendar/tasks", params={"include_done": False}).json()["data"]
    assert len(open_tasks) == 1
    assert client.delete(f"/calendar/tasks/{task['id']}").status_code == 200
    assert client.get(f"/calendar/tasks/{task['id']}").status_code == 404


def test_task_validation(client):
    assert client.post("/calendar/tasks", json={"title": ""}).status_code == 422
    response = client.post("/calendar/tasks", json={"title": "x", "priority": "urgent"})
    assert response.status_code == 422
    response = client.post("/calendar/tasks", json={"title": "x", "recurrence": "weekly"})
    assert response.status_code == 400  # recurring tasks need a due date


def test_completing_recurring_task_creates_next_one(client):
    task = make_task(client, title="Pay rent", due_date="2026-01-31", recurrence="monthly")

    response = client.post(f"/calendar/tasks/{task['id']}/complete")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "done"
    assert body["next_task"]["due_date"] == "2026-02-28"  # clamped
    assert body["next_task"]["status"] == "todo"
    assert body["next_task"]["recurrence"] == "monthly"

    assert client.post(f"/calendar/tasks/{task['id']}/complete").status_code == 400


def test_completing_one_off_task(client):
    task = make_task(client, due_date="2026-10-01")
    body = client.post(f"/calendar/tasks/{task['id']}/complete").json()
    assert body["next_task"] is None


def test_next_occurrence():
    day = datetime.date(2026, 10, 30)
    assert next_occurrence(day, "daily") == datetime.date(2026, 10, 31)
    assert next_occurrence(day, "weekly") == datetime.date(2026, 11, 6)
    assert next_occurrence(day, "monthly") == datetime.date(2026, 11, 30)
    assert next_occurrence(day, "none") is None


def test_agenda_today_and_week(client):
    make_event(client, title="Mon standup", start_at="2026-10-05T09:00:00", end_at=None)
    make_event(client, title="Wed dentist", start_at="2026-10-07T14:00:00",
               end_at="2026-10-07T15:00:00")
    make_event(client, title="Next week", start_at="2026-10-13T09:00:00", end_at=None)
    make_event(client, title="Holiday", start_at="2026-10-07T00:00:00", end_at=None, all_day=True)

    make_task(client, title="Due Wed", due_date="2026-10-07", priority="low")
    make_task(client, title="Due Wed high", due_date="2026-10-07", priority="high")
    make_task(client, title="Overdue", due_date="2026-10-01")
    done = make_task(client, title="Done", due_date="2026-10-07")
    client.post(f"/calendar/tasks/{done['id']}/complete")

    agenda = client.get("/calendar/agenda/today", params={"on": "2026-10-07"}).json()
    assert [e["title"] for e in agenda["events"]] == ["Holiday", "Wed dentist"]
    assert [t["title"] for t in agenda["tasks"]] == ["Due Wed high", "Due Wed"]
    assert [t["title"] for t in agenda["overdue_tasks"]] == ["Overdue"]

    week = client.get("/calendar/agenda/week", params={"on": "2026-10-07"}).json()
    assert week["start_date"] == "2026-10-05"
    assert week["end_date"] == "2026-10-11"
    assert [e["title"] for e in week["events"]] == ["Mon standup", "Holiday", "Wed dentist"]


def test_upcoming_uses_today(client):
    current = today()
    soon = current + datetime.timedelta(days=3)
    far = current + datetime.timedelta(days=40)
    make_event(client, title="Soon", start_at=f"{soon}T10:00:00", end_at=None)
    make_event(client, title="Far", start_at=f"{far}T10:00:00", end_at=None)
    make_task(client, title="Soon task", due_date=soon.isoformat())

    upcoming = client.get("/calendar/upcoming", params={"days": 14}).json()
    assert [e["title"] for e in upcoming["events"]] == ["Soon"]
    assert [t["title"] for t in upcoming["tasks"]] == ["Soon task"]
