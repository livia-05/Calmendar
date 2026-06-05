NAME = 'Quick walk around the block'


def _first_default(client):
    return next(b for b in client.get('/api/breaks').get_json() if not b['is_custom'])


# ── Validation ───────────────────────────────────────────────────────────────

def test_action_by_name_requires_name(client):
    r = client.post('/api/breaks/action-by-name', json={'action': 'favorite'})
    assert r.status_code == 400


def test_action_by_name_requires_action(client):
    r = client.post('/api/breaks/action-by-name', json={'name': NAME})
    assert r.status_code == 400


def test_action_by_name_rejects_unknown_action(client):
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'delete'})
    assert r.status_code == 400


def test_action_by_name_rejects_empty_body(client):
    r = client.post('/api/breaks/action-by-name', json={})
    assert r.status_code == 400


# ── Create-if-not-exists ──────────────────────────────────────────────────────

def test_action_by_name_creates_activity_when_missing(client):
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    assert r.status_code == 200
    assert r.get_json()['name'] == NAME


def test_action_by_name_new_activity_is_not_custom(client):
    # AI-suggested activities created through this route must not be is_custom —
    # they cannot be deleted by the user and should not appear in the custom list
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    assert r.get_json()['is_custom'] == 0


def test_action_by_name_does_not_create_duplicate(client):
    client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'block'})
    all_breaks = (
        client.get('/api/breaks').get_json() +
        client.get('/api/breaks/blocked').get_json()
    )
    assert sum(1 for b in all_breaks if b['name'] == NAME) == 1


def test_action_by_name_lookup_is_case_insensitive(client):
    # First call: creates 'walk outside', favorites it
    client.post('/api/breaks/action-by-name', json={'name': 'walk outside', 'action': 'favorite'})
    # Second call: 'Walk Outside' should match the existing row and toggle it off, not create a second entry
    r = client.post('/api/breaks/action-by-name', json={'name': 'Walk Outside', 'action': 'favorite'})
    assert r.get_json()['is_favorited'] == 0


# ── Favorite ─────────────────────────────────────────────────────────────────

def test_action_by_name_favorite_sets_favorited(client):
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    assert r.get_json()['is_favorited'] == 1


def test_action_by_name_favorite_toggles_off(client):
    client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    assert r.get_json()['is_favorited'] == 0


def test_action_by_name_favoriting_clears_blocked(client):
    client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'block'})
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    data = r.get_json()
    assert data['is_favorited'] == 1
    assert data['is_blocked'] == 0


# ── Block ─────────────────────────────────────────────────────────────────────

def test_action_by_name_block_sets_blocked(client):
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'block'})
    assert r.get_json()['is_blocked'] == 1


def test_action_by_name_block_toggles_off(client):
    client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'block'})
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'block'})
    assert r.get_json()['is_blocked'] == 0


def test_action_by_name_blocking_clears_favorite(client):
    client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'favorite'})
    r = client.post('/api/breaks/action-by-name', json={'name': NAME, 'action': 'block'})
    data = r.get_json()
    assert data['is_blocked'] == 1
    assert data['is_favorited'] == 0


# ── /api/breaks/blocked endpoint ──────────────────────────────────────────────

def test_blocked_breaks_empty_by_default(client):
    r = client.get('/api/breaks/blocked')
    assert r.status_code == 200
    assert r.get_json() == []


def test_blocked_break_appears_in_blocked_endpoint(client):
    b = _first_default(client)
    client.put(f'/api/breaks/{b["id"]}/block')
    blocked = client.get('/api/breaks/blocked').get_json()
    assert any(x['id'] == b['id'] for x in blocked)


def test_blocked_break_hidden_from_main_list(client):
    b = _first_default(client)
    client.put(f'/api/breaks/{b["id"]}/block')
    main = client.get('/api/breaks').get_json()
    assert not any(x['id'] == b['id'] for x in main)


def test_unblocking_removes_from_blocked_list(client):
    b = _first_default(client)
    bid = b['id']
    client.put(f'/api/breaks/{bid}/block')
    client.put(f'/api/breaks/{bid}/block')  # toggle back off
    blocked = client.get('/api/breaks/blocked').get_json()
    assert not any(x['id'] == bid for x in blocked)
