import pytest
from app.app import app, workouts

@pytest.fixture(autouse=True)
def reset_workouts():
    # Clear lists in place to preserve original dict reference
    for k in workouts.keys():
        workouts[k].clear()
    yield
    for k in workouts.keys():
        workouts[k].clear()

@pytest.fixture
def client():
    return app.test_client()

def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ACEest Fitness (Flask)" in resp.data
    for cat in workouts.keys():
        assert cat.encode() in resp.data

def test_add_session_success(client):
    resp = client.post("/add", data={"category": "Workout", "exercise": "Push Ups", "duration": "15"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Added Push Ups (15 min) to Workout!" in resp.data
    assert len(workouts["Workout"]) == 1
    assert workouts["Workout"][0]["exercise"] == "Push Ups"

def test_add_session_missing_fields(client):
    resp = client.post("/add", data={"category": "Warm-up", "exercise": "", "duration": ""}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error: exercise and duration required" in resp.data
    assert len(workouts["Warm-up"]) == 0

def test_add_session_bad_duration(client):
    resp = client.post("/add", data={"category": "Workout", "exercise": "Squats", "duration": "abc"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error: duration must be number" in resp.data
    assert len(workouts["Workout"]) == 0

def test_unknown_category_creates_new(client):
    resp = client.post("/add", data={"category": "Custom", "exercise": "Plank", "duration": "5"}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Custom" in workouts
    assert workouts["Custom"][0]["exercise"] == "Plank"

def test_summary_page(client):
    client.post("/add", data={"category": "Warm-up", "exercise": "Jog", "duration": "10"})
    client.post("/add", data={"category": "Workout", "exercise": "Push Ups", "duration": "15"})
    resp = client.get("/summary")
    assert resp.status_code == 200
    assert b"Total: 25 minutes" in resp.data

def test_chart_png(client):
    client.post("/add", data={"category": "Workout", "exercise": "Sit Ups", "duration": "12"})
    resp = client.get("/chart.png")
    assert resp.status_code == 200
    assert resp.content_type == "image/png"
    # PNG signature
    assert resp.data.startswith(b"\x89PNG")

def test_api_docs(client):
    resp = client.get("/api")
    assert resp.status_code == 200
    assert b"/api/workouts" in resp.data

def test_api_get_empty(client):
    resp = client.get("/api/workouts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "workouts" in data
    for cat in workouts.keys():
        assert data["workouts"][cat] == []

def test_api_post_success(client):
    resp = client.post("/api/workouts", json={"category": "Workout", "exercise": "Burpees", "duration": 7})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "ok"
    assert any(s["exercise"] == "Burpees" for s in workouts["Workout"])

def test_api_post_bad_payload(client):
    resp = client.post("/api/workouts", json={"exercise": "", "duration": 5})
    assert resp.status_code == 400
    assert b"exercise and duration required" in resp.data

def test_api_post_bad_duration_type(client):
    resp = client.post("/api/workouts", json={"exercise": "Jump", "duration": "x"})
    assert resp.status_code == 400
    assert b"duration must be integer" in resp.data

def test_api_summary(client):
    client.post("/api/workouts", json={"category": "Workout", "exercise": "Push Ups", "duration": 10})
    client.post("/api/workouts", json={"category": "Warm-up", "exercise": "Jog", "duration": 5})
    resp = client.get("/api/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_minutes"] == 15
    assert data["by_category"]["Workout"] == 10
    assert data["by_category"]["Warm-up"] == 5