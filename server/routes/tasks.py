from flask import Blueprint, request, jsonify
from server.database import get_db

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@tasks_bp.route('', methods=['GET'])
def get_tasks():
    date = request.args.get('date')
    db = get_db()
    if date:
        rows = db.execute(
            'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT * FROM tasks ORDER BY date, start_time'
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@tasks_bp.route('', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('date'):
        return jsonify({'error': 'title and date are required'}), 400
    db = get_db()
    cursor = db.execute(
        '''INSERT INTO tasks (title, date, start_time, end_time, notes, priority, category)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (data['title'], data['date'], data.get('start_time'), data.get('end_time'),
         data.get('notes'), data.get('priority', 'medium'), data.get('category'))
    )
    db.commit()
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify(dict(task)), 201


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = get_db().execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(dict(task))


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    db = get_db()
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is None:
        return jsonify({'error': 'Task not found'}), 404

    allowed = ['title', 'date', 'start_time', 'end_time', 'notes', 'priority', 'category', 'status']
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400

    set_clause = ', '.join(f'{k} = ?' for k in updates)
    db.execute(f'UPDATE tasks SET {set_clause} WHERE id = ?', [*updates.values(), task_id])
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()))


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db = get_db()
    if db.execute('SELECT id FROM tasks WHERE id = ?', (task_id,)).fetchone() is None:
        return jsonify({'error': 'Task not found'}), 404
    db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    return '', 204
