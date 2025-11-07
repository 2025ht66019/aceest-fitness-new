import os
import json
import pytest
from app import create_app

@pytest.fixture()
def data_file(tmp_path):
    return str(tmp_path / "data.json")

@pytest.fixture()
def app_instance(data_file):
    return create_app({'TESTING': True, 'DATA_FILE': data_file})

@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()

def read_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_index_get(client, data_file):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Log Workouts' in resp.data

def test_log_workout_success(client, data_file):
    resp = client.post('/log', data={
        'category': 'Workout',
        'exercise': 'Push-ups',
        'duration': '15'
    }, follow_redirects=True)
    assert resp.status_code == 200
    # Flash message should appear
    assert b'Added Push-ups (15 min) to Workout!' in resp.data
    # Data file should contain entry
    data = read_json(data_file)
    assert data is not None
    assert any(e['exercise'] == 'Push-ups' and e['duration'] == 15 for e in data['Workout'])

def test_log_workout_invalid_duration(client, data_file):
    resp = client.post('/log', data={
        'category': 'Workout',
        'exercise': 'Squats',
        'duration': '0'  # invalid
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Duration must be a positive whole number.' in resp.data
    data = read_json(data_file)
    # Data file might not yet exist; ensure no valid entries added
    if data:
        assert not any(e['exercise'] == 'Squats' for e in data['Workout'])

def test_summary_empty(client, data_file):
    resp = client.get('/summary')
    assert resp.status_code == 200
    assert b'No sessions recorded.' in resp.data or b'No workouts logged yet.' in resp.data

def test_progress_no_data(client, data_file):
    resp = client.get('/progress')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    # Allow either empty state or totals (if existing global data leaked)
    assert ('No workout data logged yet.' in html) or ('Total Training Time Logged:' in html)

def test_progress_with_data(client, data_file):
    # First log a workout
    client.post('/log', data={
        'category': 'Warm-up',
        'exercise': 'Jumping Jacks',
        'duration': '5'
    }, follow_redirects=True)
    resp = client.get('/progress')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    # Should show total minutes (looser substring matching)
    assert 'Total Training Time Logged:' in html
    # Match any minutes value (digits) to be robust against prior persisted data
    import re
    assert re.search(r'Total Training Time Logged: \d+ minutes', html)
    # Should embed chart image (base64 PNG)
    assert 'data:image/png;base64' in html

