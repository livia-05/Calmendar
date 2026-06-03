CUSTOM = {'name': 'Power nap', 'duration_minutes': 20, 'is_screen_free': 1, 'category': 'rest'}


def _first_default(client):
    breaks = client.get('/api/breaks').get_json()
    return next(b for b in breaks if not b['is_custom'])


def _make_custom(client):
    return client.post('/api/breaks', json=CUSTOM).get_json()


# ── List ─────────────────────────────────────────────────────────────────────

def test_default_breaks_are_seeded(client):
    r = client.get('/api/breaks')
    assert r.status_code == 200
    assert len(r.get_json()) >= 10


def test_filter_screen_free_only(client):
    r = client.get('/api/breaks?screen_free=1')
    data = r.get_json()
    assert len(data) > 0
    assert all(b['is_screen_free'] == 1 for b in data)


def test_filter_screen_not_free(client):
    r = client.get('/api/breaks?screen_free=0')
    data = r.get_json()
    assert len(data) > 0
    assert all(b['is_screen_free'] == 0 for b in data)


def test_filter_favorited_empty_by_default(client):
    r = client.get('/api/breaks?favorited=1')
    assert r.get_json() == []


# ── Create ───────────────────────────────────────────────────────────────────

def test_create_custom_break(client):
    r = client.post('/api/breaks', json=CUSTOM)
    assert r.status_code == 201
    data = r.get_json()
    assert data['name'] == 'Power nap'
    assert data['is_custom'] == 1
    assert data['duration_minutes'] == 20


def test_create_break_requires_name(client):
    r = client.post('/api/breaks', json={'duration_minutes': 10})
    assert r.status_code == 400


# ── Favorite ─────────────────────────────────────────────────────────────────

def test_toggle_favorite_on(client):
    b = _first_default(client)
    r = client.put(f'/api/breaks/{b["id"]}/favorite')
    assert r.get_json()['is_favorited'] == 1


def test_toggle_favorite_off(client):
    b = _first_default(client)
    bid = b['id']
    client.put(f'/api/breaks/{bid}/favorite')
    r = client.put(f'/api/breaks/{bid}/favorite')
    assert r.get_json()['is_favorited'] == 0


def test_favorited_break_appears_in_filter(client):
    b = _first_default(client)
    client.put(f'/api/breaks/{b["id"]}/favorite')
    r = client.get('/api/breaks?favorited=1')
    assert any(x['id'] == b['id'] for x in r.get_json())


def test_toggle_favorite_not_found(client):
    r = client.put('/api/breaks/999/favorite')
    assert r.status_code == 404


# ── Delete ───────────────────────────────────────────────────────────────────

def test_delete_default_break_is_forbidden(client):
    b = _first_default(client)
    r = client.delete(f'/api/breaks/{b["id"]}')
    assert r.status_code == 403


def test_delete_custom_break(client):
    b = _make_custom(client)
    r = client.delete(f'/api/breaks/{b["id"]}')
    assert r.status_code == 204


def test_deleted_custom_break_is_gone(client):
    b = _make_custom(client)
    bid = b['id']
    client.delete(f'/api/breaks/{bid}')
    r = client.get('/api/breaks')
    assert not any(x['id'] == bid for x in r.get_json())


def test_delete_break_not_found(client):
    r = client.delete('/api/breaks/999')
    assert r.status_code == 404
