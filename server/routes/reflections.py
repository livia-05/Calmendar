import os
import anthropic
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


@reflections_bp.route('/<date>/summary', methods=['POST'])
def generate_summary(date):
    db = get_db()
    tasks      = db.execute('SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)).fetchall()
    completed  = [t for t in tasks if t['status'] == 'completed']
    pending    = [t for t in tasks if t['status'] != 'completed']
    reflection = db.execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()

    done_list  = '\n'.join(f'- {t["title"]}' for t in completed) or 'None'
    pend_list  = '\n'.join(f'- {t["title"]}' for t in pending)  or 'None'
    mood       = reflection['mood']  if reflection else None
    notes      = reflection['notes'] if reflection else None

    prompt = f"""You are a warm, calm daily planning assistant. A user has finished their day.

Date: {date}
Mood rating: {mood}/5
User notes: {notes or 'None'}

Completed today:
{done_list}

Still pending:
{pend_list}

Write a brief, personal end-of-day summary (3–4 sentences total):
1. Acknowledge what was accomplished.
2. Gently note anything left for tomorrow (if anything).
3. Close with one warm, encouraging sentence.

Tone: calm, genuine, supportive. Address the user as "you". No bullet points."""

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY is not set'}), 500

    try:
        client  = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            messages=[{'role': 'user', 'content': prompt}]
        )
        summary = message.content[0].text
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    if reflection:
        db.execute('UPDATE reflections SET ai_summary = ? WHERE date = ?', (summary, date))
    else:
        db.execute('INSERT INTO reflections (date, ai_summary) VALUES (?, ?)', (date, summary))
    db.commit()

    row = db.execute('SELECT * FROM reflections WHERE date = ?', (date,)).fetchone()
    return jsonify(dict(row))
