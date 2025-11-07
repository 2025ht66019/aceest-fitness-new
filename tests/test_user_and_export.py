import re
import io
from app import create_app
import pytest

@pytest.fixture()
def data_file(tmp_path):
    return str(tmp_path / "data.json")

@pytest.fixture()
def user_file(tmp_path):
    return str(tmp_path / "user.json")

@pytest.fixture()
def app_instance(data_file, user_file):
    # TESTING disables CSRF, easier form posts
    return create_app({'TESTING': True, 'DATA_FILE': data_file, 'USER_FILE': user_file})

@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()

def test_user_get_empty(client):
    resp = client.get('/user')
    assert resp.status_code == 200
    # Heading from user.html
    assert b'User Information' in resp.data

def test_user_save_invalid(client):
    # Invalid gender + out of range height triggers multiple errors
    resp = client.post('/user/save', data={
        'name': 'Test', 'regn_id': 'R1', 'age': '30', 'gender': 'X', 'height': '10', 'weight': '10'
    }, follow_redirects=True)
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')
    assert 'Gender must be M or F.' in body
    assert 'Height out of range' in body

def test_user_save_success(client):
    resp = client.post('/user/save', data={
        'name': 'Alice', 'regn_id': 'REG123', 'age': '28', 'gender': 'F', 'height': '165', 'weight': '60'
    }, follow_redirects=True)
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')
    assert 'User info saved! BMI=' in body
    # subsequent GET should include BMI line
    get_resp = client.get('/user')
    assert get_resp.status_code == 200
    assert 'BMI:' in get_resp.data.decode('utf-8')

def test_log_workout_with_user(client):
    # Ensure calories included after user saved
    client.post('/user/save', data={
        'name': 'Bob', 'regn_id': 'X1', 'age': '35', 'gender': 'M', 'height': '180', 'weight': '80'
    })
    resp = client.post('/log', data={'category': 'Workout', 'exercise': 'Push-ups', 'duration': '10'}, follow_redirects=True)
    assert resp.status_code == 200
    # Check flash presence
    assert b'Added Push-ups (10 min) to Workout!' in resp.data
    summary = client.get('/summary')
    assert summary.status_code == 200
    html = summary.data.decode('utf-8')
    assert 'Push-ups' in html
    assert re.search(r'Push-ups</strong> - 10 min / .* kcal', html)

def test_export_pdf(client):
    # Add a workout to ensure table has at least one row
    client.post('/log', data={'category': 'Warm-up', 'exercise': 'Jumping Jacks', 'duration': '5'})
    pdf_resp = client.get('/export')
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers.get('Content-Type', '').startswith('application/pdf')
    # First few bytes of PDF
    start = pdf_resp.data[:4]
    assert start == b'%PDF'
