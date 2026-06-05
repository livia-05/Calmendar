DATE = '2026-06-02'


def _make_task(client, title, status='not_started'):
    r = client.post('/api/tasks', json={'title': title, 'date': DATE})
    tid = r.get_json()['id']
    if status != 'not_started':
        client.put(f'/api/tasks/{tid}', json={'status': status})
    return r.get_json()


# ── Get ──────────────────────────────────────────────────────────────────────

def test_get_reflection_not_found(client):
    r = client.get(f'/api/reflections/{DATE}')
    assert r.status_code == 200
    assert r.get_json() is None


def test_list_reflections_empty(client):
    r = client.get('/api/reflections')
    assert r.status_code == 200
    assert r.get_json() == []


# ── Create ───────────────────────────────────────────────────────────────────

def test_create_reflection_returns_201(client):
    r = client.post('/api/reflections', json={'date': DATE, 'mood': 4})
    assert r.status_code == 201


def test_create_reflection_stores_mood_and_notes(client):
    r = client.post('/api/reflections', json={'date': DATE, 'mood': 3, 'notes': 'Productive day'})
    data = r.get_json()
    assert data['mood'] == 3
    assert data['notes'] == 'Productive day'


def test_create_reflection_requires_date(client):
    r = client.post('/api/reflections', json={'mood': 4})
    assert r.status_code == 400


def test_reflection_date_must_be_unique(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 3})
    r = client.post('/api/reflections', json={'date': DATE, 'mood': 5})
    assert r.status_code != 201


# ── Update ───────────────────────────────────────────────────────────────────

def test_update_reflection_mood(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 2})
    r = client.put(f'/api/reflections/{DATE}', json={'mood': 5})
    assert r.get_json()['mood'] == 5


def test_update_reflection_notes(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 3})
    r = client.put(f'/api/reflections/{DATE}', json={'notes': 'Updated thoughts'})
    assert r.get_json()['notes'] == 'Updated thoughts'


def test_update_reflection_not_found(client):
    r = client.put(f'/api/reflections/{DATE}', json={'mood': 4})
    assert r.status_code == 404


# ── Summary ───────────────────────────────────────────────────────────────────

def test_summary_is_saved_to_reflection(client):
    _make_task(client, 'Exercise', status='completed')
    _make_task(client, 'Read', status='not_started')
    client.post('/api/reflections', json={'date': DATE, 'mood': 4})
    r = client.post(f'/api/reflections/{DATE}/summary')
    assert r.status_code == 200
    assert r.get_json()['ai_summary'] is not None


def test_summary_creates_reflection_if_missing(client):
    _make_task(client, 'Write code', status='completed')
    r = client.post(f'/api/reflections/{DATE}/summary')
    assert r.status_code == 200
    row = client.get(f'/api/reflections/{DATE}').get_json()
    assert row['ai_summary'] is not None


def test_summary_persists_on_get(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 3})
    client.post(f'/api/reflections/{DATE}/summary')
    r = client.get(f'/api/reflections/{DATE}')
    assert r.get_json()['ai_summary'] is not None


# ── Uniqueness constraint ─────────────────────────────────────────────────────

def test_duplicate_reflection_returns_409(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 3})
    r = client.post('/api/reflections', json={'date': DATE, 'mood': 5})
    assert r.status_code == 409


def test_duplicate_reflection_error_body(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 3})
    r = client.post('/api/reflections', json={'date': DATE, 'mood': 5})
    assert 'error' in r.get_json()


# ── Future date rejection ─────────────────────────────────────────────────────

FUTURE = '2099-01-01'


def test_create_reflection_future_date_rejected(client):
    r = client.post('/api/reflections', json={'date': FUTURE, 'mood': 3})
    assert r.status_code == 400


def test_update_reflection_future_date_rejected(client):
    r = client.put(f'/api/reflections/{FUTURE}', json={'mood': 3})
    assert r.status_code == 400


# ── Update validation ─────────────────────────────────────────────────────────

def test_update_reflection_no_valid_fields_returns_400(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 3})
    r = client.put(f'/api/reflections/{DATE}', json={'unknown_field': 'value'})
    assert r.status_code == 400


def test_update_reflection_all_three_valid_fields(client):
    client.post('/api/reflections', json={'date': DATE, 'mood': 1, 'notes': 'rough start'})
    r = client.put(f'/api/reflections/{DATE}', json={
        'mood': 5, 'notes': 'turned around', 'ai_summary': 'A good recovery day.'
    })
    data = r.get_json()
    assert data['mood'] == 5
    assert data['notes'] == 'turned around'
    assert data['ai_summary'] == 'A good recovery day.'
