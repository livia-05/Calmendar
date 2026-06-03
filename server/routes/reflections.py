from flask import Blueprint, request, jsonify
from server.database import get_db

reflections_bp = Blueprint('reflections', __name__, url_prefix='/api/reflections')


@reflections_bp.route('', methods=['GET'])
def get_reflections():
    rows = get_db().execute('SELECT * FROM reflections ORDER BY date DESC').fetchall()
    return jsonify([dict(r) for r in rows])


@reflections_bp.route('/<date>', methods=['GET'])
def get_reflection(date):
    row = get_db().execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()
    return jsonify(dict(row) if row else None)


@reflections_bp.route('', methods=['POST'])
def create_reflection():
    data = request.get_json()
    if not data or not data.get('date'):
        return jsonify({'error': 'date is required'}), 400
    db = get_db()
    cursor = db.execute(
        'INSERT INTO reflections (date, mood, notes, ai_summary) VALUES (?, ?, ?, ?)',
        (data['date'], data.get('mood'), data.get('notes'), data.get('ai_summary'))
    )
    db.commit()
    row = db.execute('SELECT * FROM reflections WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@reflections_bp.route('/<date>', methods=['PUT'])
def update_reflection(date):
    data = request.get_json()
    db = get_db()
    row = db.execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()
    if row is None:
        return jsonify({'error': 'Reflection not found'}), 404

    updates = {k: data[k] for k in ['mood', 'notes', 'ai_summary'] if k in data}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    set_clause = ', '.join(f'{k} = ?' for k in updates)
    db.execute(f'UPDATE reflections SET {set_clause} WHERE date = ?', [*updates.values(), date])
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()))
