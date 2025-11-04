import re
import pytest

# Import the Flask app objects
from app.app import app, workouts

@pytest.fixture(autouse=True)
def _reset_workouts():
    # Clear workouts before each test
    for k in list(workouts.keys()):
        workouts[k].clear()
    yield

@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()

def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ACEest Fitness & Gym Tracker" in resp.data

def test_add_session_success(client):
    data = {"category": "Workout", "exercise": "Push Ups", "duration": "15"}
    resp = client.post("/add", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Added Push Ups (15 min) to Workout!" in resp.data
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Push Ups"

def test_add_session_missing_exercise(client):
    data = {"category": "Warm-up", "exercise": "", "duration": "5"}
    resp = client.post("/add", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error: exercise and duration required" in resp.data
    assert len(workouts["Warm-up"]) == 0

def test_add_session_bad_duration(client):
    data = {"category": "Workout", "exercise": "Squats", "duration": "abc"}
    resp = client.post("/add", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error: duration must be a number" in resp.data
    assert len(workouts["Workout"]) == 0

def test_summary_page_empty(client):
    resp = client.get("/summary")
    assert resp.status_code == 200
    # Should show empty state
    assert b"No sessions recorded." in resp.data

def test_summary_page_with_entries(client):
    client.post("/add", data={"category": "Workout", "exercise": "Plank", "duration": "10"}, follow_redirects=True)
    client.post("/add", data={"category": "Cool-down", "exercise": "Stretch", "duration": "5"}, follow_redirects=True)
    resp = client.get("/summary")
    assert resp.status_code == 200
    assert b"Plank - 10 min" in resp.data
    assert b"Stretch - 5 min" in resp.data
    # Total time calculation (10 + 5)
    assert re.search(rb"Total Time Spent:\s+15 minutes", resp.data)

def test_unknown_category_adds_new_list(client):
    client.post("/add", data={"category": "Custom", "exercise": "Balance", "duration": "3"}, follow_redirects=True)
    assert "Custom" in workouts
    assert len(workouts["Custom"]) == 1
