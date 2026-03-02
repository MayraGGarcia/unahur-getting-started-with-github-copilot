import copy

import pytest
from fastapi.testclient import TestClient

from src import app
from src.app import activities


client = TestClient(app.app)

# preserve original state so tests can restore
initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the shared in-memory activities dictionary before each test."""
    activities.clear()
    activities.update(copy.deepcopy(initial_activities))


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_success():
    email = "newstudent@mergington.edu"
    activity = "Chess Club"
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert email in response.json()["message"]


def test_signup_activity_not_found():
    response = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    assert response.status_code == 404


def test_signup_already_signed():
    activity = "Chess Club"
    email = "repeat@mergington.edu"
    # first signup should succeed
    response1 = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response1.status_code == 200
    # second attempt with same address fails
    response2 = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response2.status_code == 400


def test_signup_multiple_students():
    activity = "Science Club"
    emails = ["one@school.edu", "two@school.edu"]
    for e in emails:
        resp = client.post(f"/activities/{activity}/signup", params={"email": e})
        assert resp.status_code == 200
    assert activities[activity]["participants"] == emails


def test_remove_participant_success():
    activity = "Chess Club"
    participant = "student@mergington.edu"
    # ensure the participant is signed up first
    signup = client.post(f"/activities/{activity}/signup", params={"email": participant})
    assert signup.status_code == 200
    response = client.delete(f"/activities/{activity}/participants", params={"email": participant})
    assert response.status_code == 200
    assert participant not in activities[activity]["participants"]


def test_remove_participant_activity_not_found():
    response = client.delete("/activities/Fake/participants", params={"email": "x@y.com"})
    assert response.status_code == 404


def test_remove_participant_not_inscribed():
    activity = "Chess Club"
    response = client.delete(f"/activities/{activity}/participants", params={"email": "not@here.edu"})
    assert response.status_code == 404
