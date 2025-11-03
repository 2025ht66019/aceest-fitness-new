import pytest
from app import app, workouts

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear workouts before each test
        workouts.clear()
        yield client

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"ACEestFitness and Gym" in response.data

def test_add_workout_success(client):
    response = client.post('/add', data={"workout": "Running", "duration": "30"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Running - 30 minutes" in response.data
    assert any(w['workout'] == "Running" and w['duration'] == 30 for w in workouts)

def test_add_workout_missing_fields(client):
    response = client.post('/add', data={"workout": "", "duration": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please enter both workout and duration." in response.data

def test_add_workout_invalid_duration(client):
    response = client.post('/add', data={"workout": "Cycling", "duration": "abc"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Duration must be a number." in response.data
    assert not any(w['workout'] == "Cycling" for w in workouts)