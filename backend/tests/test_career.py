import datetime

from app.services.dates import now


def make_app(client, **values):
    payload = {"company": "Acme Cloud", "title": "DevOps Engineer", "work_mode": "remote"}
    payload.update(values)
    response = client.post("/career/applications", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_applications_crud_and_filters(client):
    app_ = make_app(client, salary_min=120000, salary_max=150000,
                    url="https://jobs.example.com/1", applied_date="2026-09-20")
    assert app_["status"] == "applied"
    assert app_["salary_max"] == 150000

    make_app(client, company="Hybrid Co", work_mode="hybrid", status="interview")
    default_date = make_app(client, company="NoDate Inc")
    assert default_date["applied_date"] is not None

    assert len(client.get("/career/applications").json()["data"]) == 3
    remote = client.get("/career/applications", params={"work_mode": "remote"}).json()["data"]
    assert len(remote) == 2
    interviewing = client.get("/career/applications", params={"status": "interview"}).json()
    assert [a["company"] for a in interviewing["data"]] == ["Hybrid Co"]

    response = client.patch(f"/career/applications/{app_['id']}", json={"status": "screen"})
    assert response.json()["data"]["status"] == "screen"

    assert client.get(f"/career/applications/{app_['id']}").status_code == 200
    assert client.delete(f"/career/applications/{app_['id']}").status_code == 200
    assert client.get(f"/career/applications/{app_['id']}").status_code == 404


def test_application_validation(client):
    response = client.post("/career/applications", json={
        "company": "X", "title": "Y", "salary_min": 200000, "salary_max": 100000,
    })
    assert response.status_code == 422

    response = client.post("/career/applications", json={
        "company": "X", "title": "Y", "status": "ghosted",
    })
    assert response.status_code == 422

    app_ = make_app(client, salary_min=100000)
    response = client.patch(f"/career/applications/{app_['id']}", json={"salary_max": 50000})
    assert response.status_code == 400


def test_interviews_and_cascade_delete(client):
    app_ = make_app(client)

    response = client.post("/career/interviews", json={
        "application_id": 999, "scheduled_at": "2026-10-10T10:00:00", "stage": "technical",
    })
    assert response.status_code == 400

    response = client.post("/career/interviews", json={
        "application_id": app_["id"], "scheduled_at": "2026-10-10T10:00:00",
        "stage": "recruiter_screen",
    })
    assert response.status_code == 201
    interview = response.json()["data"]
    assert interview["company"] == "Acme Cloud"
    assert interview["outcome"] == "pending"

    response = client.patch(f"/career/interviews/{interview['id']}", json={"outcome": "passed"})
    assert response.json()["data"]["outcome"] == "passed"

    detail = client.get(f"/career/applications/{app_['id']}").json()
    assert len(detail["interviews"]) == 1

    client.delete(f"/career/applications/{app_['id']}")
    assert client.get("/career/interviews").json()["data"] == []


def test_contacts_link_survives_application_delete(client):
    app_ = make_app(client)
    response = client.post("/career/contacts", json={
        "name": "Jane Recruiter", "company": "Acme Cloud", "application_id": app_["id"],
    })
    assert response.status_code == 201
    contact = response.json()["data"]

    linked = client.get("/career/contacts", params={"application_id": app_["id"]}).json()
    assert len(linked["data"]) == 1

    client.delete(f"/career/applications/{app_['id']}")
    contacts = client.get("/career/contacts").json()["data"]
    assert contacts[0]["application_id"] is None

    response = client.patch(f"/career/contacts/{contact['id']}", json={"email": "jane@acme.io"})
    assert response.json()["data"]["email"] == "jane@acme.io"
    assert client.delete(f"/career/contacts/{contact['id']}").status_code == 200

    response = client.post("/career/contacts", json={"name": "X", "application_id": 12345})
    assert response.status_code == 400


def test_certifications(client):
    response = client.post("/career/certifications", json={
        "name": "AWS Solutions Architect Associate", "provider": "AWS",
        "target_date": "2026-12-15",
    })
    assert response.status_code == 201
    cert = response.json()["data"]
    assert cert["status"] == "planned"

    client.post("/career/certifications", json={"name": "CKA"})  # no target date
    names = [c["name"] for c in client.get("/career/certifications").json()["data"]]
    assert names == ["AWS Solutions Architect Associate", "CKA"]

    response = client.patch(f"/career/certifications/{cert['id']}", json={"status": "completed"})
    assert response.json()["data"]["completed_date"] is not None

    assert client.delete(f"/career/certifications/{cert['id']}").status_code == 200


def test_pipeline_counts(client):
    for status in ["applied", "applied", "screen", "interview", "offer", "rejected", "withdrawn"]:
        make_app(client, status=status)

    app_ = client.get("/career/applications", params={"status": "interview"}).json()["data"][0]
    soon = now() + datetime.timedelta(days=2)
    client.post("/career/interviews", json={
        "application_id": app_["id"], "scheduled_at": soon.isoformat(), "stage": "technical",
    })
    client.post("/career/interviews", json={
        "application_id": app_["id"],
        "scheduled_at": (now() - datetime.timedelta(days=2)).isoformat(),
        "stage": "screen",
    })

    pipeline = client.get("/career/pipeline").json()
    assert pipeline["counts"] == {
        "applied": 2, "screen": 1, "interview": 1, "offer": 1, "rejected": 1, "withdrawn": 1,
    }
    assert pipeline["total"] == 7
    assert pipeline["active"] == 5
    # 4 of 7 got a response (screen, interview, offer, rejected)
    assert pipeline["response_rate"] == 57.1
    assert [i["stage"] for i in pipeline["upcoming_interviews"]] == ["technical"]


def test_empty_pipeline(client):
    pipeline = client.get("/career/pipeline").json()
    assert pipeline["total"] == 0
    assert pipeline["response_rate"] is None
    assert set(pipeline["counts"]) == {
        "applied", "screen", "interview", "offer", "rejected", "withdrawn",
    }
