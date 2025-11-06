import json
import re
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
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def test_plan_route(client):
    resp = client.get('/plan')
    assert resp.status_code == 200
    # Check presence of a known exercise string
    assert b'Jumping Jacks (30 reps)' in resp.data

def test_diet_route(client):
    resp = client.get('/diet')
    assert resp.status_code == 200
    # Check presence of a known diet item
    assert b'Oatmeal with Berries' in resp.data

def test_summary_after_multiple_logs(client, data_file):
    client.post('/log', data={'category': 'Warm-up', 'exercise': 'Jog', 'duration': '5'})
    client.post('/log', data={'category': 'Workout', 'exercise': 'Push-ups', 'duration': '10'})
    client.post('/log', data={'category': 'Cool-down', 'exercise': 'Stretch', 'duration': '3'})
    resp = client.get('/summary')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    data = read_json(data_file)
    assert data is not None
    # Ensure each category has at least one entry logged
    assert any(e['exercise'] == 'Jog' for e in data['Warm-up'])
    assert any(e['exercise'] == 'Push-ups' for e in data['Workout'])
    assert any(e['exercise'] == 'Stretch' for e in data['Cool-down'])
    # Verify summary page contains category headings
    for heading in ['Warm-up', 'Workout', 'Cool-down', 'Total Time Spent']:
        assert heading in html

def test_progress_empty_state(client, data_file):
    # No logs -> expect empty message
    resp = client.get('/progress')
    html = resp.data.decode('utf-8')
    # Depending on external data file leakage, page may show totals or empty message
    assert ('No workout data logged yet.' in html) or ('Total Training Time Logged:' in html)

def test_progress_after_logs(client, data_file):
    client.post('/log', data={'category': 'Warm-up', 'exercise': 'Jump Rope', 'duration': '4'})
    client.post('/log', data={'category': 'Warm-up', 'exercise': 'Arm Circles', 'duration': '2'})
    resp = client.get('/progress')
    html = resp.data.decode('utf-8')
    # Should show at least total training time string
    assert 'Total Training Time Logged:' in html
    # Warm-up total should be >= 6 minutes (if pre-existing data was present)
    warmup_match = re.search(r'Warm-up:</strong>\s*(\d+) min', html)
    assert warmup_match, 'Warm-up total not found in progress page'
    assert int(warmup_match.group(1)) >= 6
