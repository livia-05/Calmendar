from flask import Blueprint, request, jsonify
from server.database import get_db

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

_FIELDS = ['name', 'work_description', 'hobbies', 'wake_time', 'sleep_time',
           'max_daily_hours', 'break_style', 'stress_sensitivity', 'onboarding_complete']


@profile_bp.route('', methods=['GET'])
def get_profile():
    profile = get_db().execute(
        'SELECT * FROM user_profile ORDER BY id LIMIT 1'
    ).fetchone()
    return jsonify(dict(profile) if profile else None)


@profile_bp.route('', methods=['POST'])
def create_profile():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    db = get_db()
    cursor = db.execute(
        '''INSERT INTO user_profile
           (name, work_description, hobbies, wake_time, sleep_time,
            max_daily_hours, break_style, stress_sensitivity, onboarding_complete)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
        (data['name'], data.get('work_description'), data.get('hobbies'),
         data.get('wake_time'), data.get('sleep_time'), data.get('max_daily_hours', 8),
         data.get('break_style', 'frequent_short'), data.get('stress_sensitivity', 'medium'))
    )
    db.commit()
    profile = db.execute('SELECT * FROM user_profile WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify(dict(profile)), 201


@profile_bp.route('', methods=['PUT'])
def update_profile():
    data = request.get_json()
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    if profile is None:
        return jsonify({'error': 'No profile found'}), 404

    updates = {k: data[k] for k in _FIELDS if k in data}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    set_clause = ', '.join(f'{k} = ?' for k in updates)
    db.execute(f'UPDATE user_profile SET {set_clause} WHERE id = ?', [*updates.values(), profile['id']])
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM user_profile WHERE id = ?', (profile['id'],)).fetchone()))
