import random
import sqlite3
from datetime import date as _date, timedelta
from flask import Blueprint, request, jsonify
from server.database import get_db


def _cleanup_old_reflections(db):
    cutoff = (_date.today() - timedelta(days=7)).isoformat()
    db.execute('DELETE FROM reflections WHERE date < ?', (cutoff,))
    db.commit()

_CLOSERS = [
    "Rest well tonight — you showed up today and that's what matters.",
    "Progress, not perfection, is what moves you forward. Keep going.",
    "Small steps every day lead to big changes over time.",
    "Tomorrow is a fresh start, and you're already more prepared than you know.",
    "It's okay if everything didn't go as planned — that's just part of being human.",
    "Your effort today plants seeds for a better tomorrow.",
    "Every task you tackle, big or small, is a step in the right direction.",
    "You're doing better than you think. Take a breath and be proud.",
    "Consistency beats intensity — showing up daily is the whole game.",
    "Be kind to yourself tonight. You did what you could with what you had.",
]


def _build_summary(completed, pending):
    parts = []

    if completed:
        if len(completed) == 1:
            parts.append(f'You completed "{completed[0]["title"]}" today — nice work.')
        else:
            listed = ', '.join(f'"{t["title"]}"' for t in completed[:2])
            extra  = f' and {len(completed) - 2} more' if len(completed) > 2 else ''
            parts.append(f'You wrapped up {len(completed)} tasks today, including {listed}{extra}.')
    else:
        parts.append('Today was a lighter day in terms of completed tasks — and that\'s okay.')

    if pending:
        if len(pending) == 1:
            parts.append(f'"{pending[0]["title"]}" is still on your list for tomorrow.')
        else:
            parts.append(f'{len(pending)} tasks are still ahead — you can pick those up tomorrow fresh.')
    else:
        parts.append('Everything on your list is done — that\'s a great feeling.')

    parts.append(random.choice(_CLOSERS))
    return ' '.join(parts)

reflections_bp = Blueprint('reflections', __name__, url_prefix='/api/reflections')


@reflections_bp.route('', methods=['GET'])
def get_reflections():
    db = get_db()
    _cleanup_old_reflections(db)
    rows = db.execute('SELECT * FROM reflections ORDER BY date DESC').fetchall()
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
    if data['date'] > _date.today().isoformat():
        return jsonify({'error': 'Cannot create a reflection for a future date'}), 400
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO reflections (date, mood, notes, ai_summary) VALUES (?, ?, ?, ?)',
            (data['date'], data.get('mood'), data.get('notes'), data.get('ai_summary'))
        )
    except sqlite3.IntegrityError:
        return jsonify({'error': 'A reflection for this date already exists'}), 409
    db.commit()
    row = db.execute('SELECT * FROM reflections WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@reflections_bp.route('/<date>', methods=['PUT'])
def update_reflection(date):
    if date > _date.today().isoformat():
        return jsonify({'error': 'Cannot update a reflection for a future date'}), 400
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


@reflections_bp.route('/<date>/summary', methods=['POST'])
def generate_summary(date):
    if date > _date.today().isoformat():
        return jsonify({'error': 'Cannot generate a summary for a future date'}), 400
    db         = get_db()
    tasks      = db.execute('SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)).fetchall()
    completed  = [t for t in tasks if t['status'] == 'completed']
    pending    = [t for t in tasks if t['status'] != 'completed']
    reflection = db.execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()

    mood  = reflection['mood']  if reflection else None
    notes = reflection['notes'] if reflection else None

    try:
        from server.ai import generate_day_summary
        summary = generate_day_summary(date, completed, pending, mood, notes)
    except Exception:
        summary = _build_summary(completed, pending)

    if reflection:
        db.execute('UPDATE reflections SET ai_summary = ? WHERE date = ?', (summary, date))
    else:
        db.execute('INSERT INTO reflections (date, ai_summary) VALUES (?, ?)', (date, summary))
    db.commit()

    row = db.execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()
    return jsonify(dict(row))
