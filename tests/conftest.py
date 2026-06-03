import os
import tempfile
import pytest
from server.app import create_app


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    application = create_app({'TESTING': True, 'DATABASE': db_path})
    yield application
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def task(client):
    r = client.post('/api/tasks', json={'title': 'Sample task', 'date': '2026-06-02'})
    return r.get_json()


@pytest.fixture
def profile(client):
    r = client.post('/api/profile', json={
        'name': 'Test User',
        'work_description': 'Software engineer',
        'hobbies': 'Hiking',
        'wake_time': '07:00',
        'sleep_time': '23:00',
    })
    return r.get_json()
