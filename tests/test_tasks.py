import pytest


DATE = '2026-06-02'


# ── Create ──────────────────────────────────────────────────────────────────

def test_create_task_returns_201(client):
    r = client.post('/api/tasks', json={'title': 'Write tests', 'date': DATE})
    assert r.status_code == 201


def test_create_task_defaults(client):
    r = client.post('/api/tasks', json={'title': 'My task', 'date': DATE})
    data = r.get_json()
    assert data['status'] == 'not_started'
    assert data['priority'] == 'medium'
    assert data['start_time'] is None
    assert data['end_time'] is None


def test_create_task_with_times(client):
    r = client.post('/api/tasks', json={
        'title': 'Morning standup', 'date': DATE,
        'start_time': '09:00', 'end_time': '09:30', 'priority': 'high',
    })
    data = r.get_json()
    assert data['start_time'] == '09:00'
    assert data['end_time'] == '09:30'
    assert data['priority'] == 'high'


def test_create_task_requires_title(client):
    r = client.post('/api/tasks', json={'date': DATE})
    assert r.status_code == 400


def test_create_task_requires_date(client):
    r = client.post('/api/tasks', json={'title': 'No date'})
    assert r.status_code == 400


# ── Read ─────────────────────────────────────────────────────────────────────

def test_list_tasks_empty(client):
    r = client.get(f'/api/tasks?date={DATE}')
    assert r.status_code == 200
    assert r.get_json() == []


def test_list_tasks_filtered_by_date(client):
    client.post('/api/tasks', json={'title': 'Day A task', 'date': '2026-06-01'})
    client.post('/api/tasks', json={'title': 'Day B task', 'date': '2026-06-02'})
    r = client.get('/api/tasks?date=2026-06-01')
    data = r.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Day A task'


def test_list_all_tasks(client):
    client.post('/api/tasks', json={'title': 'Task 1', 'date': '2026-06-01'})
    client.post('/api/tasks', json={'title': 'Task 2', 'date': '2026-06-02'})
    r = client.get('/api/tasks')
    assert len(r.get_json()) == 2


def test_get_task(client, task):
    r = client.get(f'/api/tasks/{task["id"]}')
    assert r.status_code == 200
    assert r.get_json()['title'] == 'Sample task'


def test_get_task_not_found(client):
    r = client.get('/api/tasks/999')
    assert r.status_code == 404


# ── Update ───────────────────────────────────────────────────────────────────

def test_update_task_title(client, task):
    r = client.put(f'/api/tasks/{task["id"]}', json={'title': 'Updated title'})
    assert r.status_code == 200
    assert r.get_json()['title'] == 'Updated title'


def test_update_task_status_to_in_progress(client, task):
    r = client.put(f'/api/tasks/{task["id"]}', json={'status': 'in_progress'})
    assert r.get_json()['status'] == 'in_progress'


def test_update_task_status_to_completed(client, task):
    r = client.put(f'/api/tasks/{task["id"]}', json={'status': 'completed'})
    assert r.get_json()['status'] == 'completed'


def test_status_cycles_through_all_states(client, task):
    tid = task['id']
    for expected in ['in_progress', 'completed', 'not_started']:
        client.put(f'/api/tasks/{tid}', json={'status': expected})
        r = client.get(f'/api/tasks/{tid}')
        assert r.get_json()['status'] == expected


def test_update_task_not_found(client):
    r = client.put('/api/tasks/999', json={'title': 'Ghost'})
    assert r.status_code == 404


def test_update_task_no_valid_fields(client, task):
    r = client.put(f'/api/tasks/{task["id"]}', json={'unknown_field': 'value'})
    assert r.status_code == 400


# ── Delete ───────────────────────────────────────────────────────────────────

def test_delete_task(client, task):
    r = client.delete(f'/api/tasks/{task["id"]}')
    assert r.status_code == 204


def test_deleted_task_is_gone(client, task):
    tid = task['id']
    client.delete(f'/api/tasks/{tid}')
    r = client.get(f'/api/tasks/{tid}')
    assert r.status_code == 404


def test_delete_task_not_found(client):
    r = client.delete('/api/tasks/999')
    assert r.status_code == 404
