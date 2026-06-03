FULL_PROFILE = {
    'name': 'Alex',
    'work_description': 'Software engineer who stares at screens all day',
    'hobbies': 'Hiking, reading, cooking',
    'wake_time': '07:00',
    'sleep_time': '23:00',
    'max_daily_hours': 7,
    'break_style': 'frequent_short',
    'stress_sensitivity': 'medium',
}


# ── Get ──────────────────────────────────────────────────────────────────────

def test_get_profile_when_empty(client):
    r = client.get('/api/profile')
    assert r.status_code == 200
    assert r.get_json() is None


# ── Create ───────────────────────────────────────────────────────────────────

def test_create_profile_returns_201(client):
    r = client.post('/api/profile', json={'name': 'Alex'})
    assert r.status_code == 201


def test_create_profile_sets_onboarding_complete(client):
    r = client.post('/api/profile', json=FULL_PROFILE)
    assert r.get_json()['onboarding_complete'] == 1


def test_create_profile_stores_all_fields(client):
    r = client.post('/api/profile', json=FULL_PROFILE)
    data = r.get_json()
    assert data['name'] == 'Alex'
    assert data['work_description'] == FULL_PROFILE['work_description']
    assert data['hobbies'] == FULL_PROFILE['hobbies']
    assert data['max_daily_hours'] == 7


def test_create_profile_requires_name(client):
    r = client.post('/api/profile', json={'work_description': 'Engineer'})
    assert r.status_code == 400


def test_get_profile_after_creation(client):
    client.post('/api/profile', json={'name': 'Alex'})
    r = client.get('/api/profile')
    assert r.status_code == 200
    assert r.get_json()['name'] == 'Alex'


# ── Update ───────────────────────────────────────────────────────────────────

def test_update_profile_name(client, profile):
    r = client.put('/api/profile', json={'name': 'Alex Renamed'})
    assert r.status_code == 200
    assert r.get_json()['name'] == 'Alex Renamed'


def test_update_profile_max_hours(client, profile):
    r = client.put('/api/profile', json={'max_daily_hours': 6})
    assert r.get_json()['max_daily_hours'] == 6


def test_update_profile_not_found(client):
    r = client.put('/api/profile', json={'name': 'Nobody'})
    assert r.status_code == 404
