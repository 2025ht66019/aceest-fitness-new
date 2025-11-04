import re
import pytest
from app.app import app, workouts

@pytest.fixture(autouse=True)
def clear_workouts():
    # Reset global workouts before each test
    for k in list(workouts.keys()):
        workouts[k].clear()
    yield
    for k in list(workouts.keys()):
        workouts[k].clear()

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ACEest Fitness & Gym Tracker" in resp.data
    # Should list categories even when empty
    for cat in workouts.keys():
        assert cat.encode() in resp.data

def test_add_session_success(client):
    data = {"category": "Workout", "exercise": "Push Ups", "duration": "15"}
    resp = client.post("/add", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Added Push Ups (15 min) to Workout!" in resp.data
    assert any(s["exercise"] == "Push Ups" for s in workouts["Workout"])

def test_add_session_missing_exercise(client):
    resp = client.post("/add", data={"category": "Warm-up", "exercise": "", "duration": "5"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error: exercise and duration required" in resp.data
    assert len(workouts["Warm-up"]) == 0

def test_add_session_bad_duration(client):
    resp = client.post("/add", data={"category": "Workout", "exercise": "Squats", "duration": "abc"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error: duration must be a number" in resp.data
    assert len(workouts["Workout"]) == 0

def test_summary_page_empty(client):
    resp = client.get("/summary")
    assert resp.status_code == 200
    assert b"Total Time Spent: 0 minutes" in resp.data
    # Empty message appears for at least one category
    assert b"No sessions recorded." in resp.data

def test_summary_page_with_entries(client):
    client.post("/add", data={"category": "Workout", "exercise": "Plank", "duration": "10"}, follow_redirects=True)
    client.post("/add", data={"category": "Cool-down", "exercise": "Stretch", "duration": "5"}, follow_redirects=True)
    resp = client.get("/summary")
    assert resp.status_code == 200
    assert b"Plank - 10 min" in resp.data
    assert b"Stretch - 5 min" in resp.data
    assert re.search(rb"Total Time Spent:\s+15 minutes", resp.data)

def test_unknown_category_adds_new_list(client):
    client.post("/add", data={"category": "Custom", "exercise": "Balance", "duration": "7"}, follow_redirects=True)
    assert "Custom" in workouts
    assert workouts["Custom"][0]["exercise"] == "Balance"

def test_workout_chart_route(client):
    resp = client.get("/chart")
    assert resp.status_code == 200
    assert b"Personalized Workout Chart" in resp.data
    # Check one item from each section
    assert b"Jumping Jacks" in resp.data
    assert b"Burpees" in resp.data
    assert b"Yoga Poses" in resp.data

def test_diet_chart_route(client):
    resp = client.get("/diet")
    assert resp.status_code == 200
    assert b"Best Diet Chart for Fitness Goals" in resp.data
    assert b"Grilled Chicken Salad" in resp.data
    assert b"Protein Shake" in resp.data
    assert b"Trail Mix" in resp.data