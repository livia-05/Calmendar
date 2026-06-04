from flask import Blueprint, request, jsonify
from server.database import get_db

breaks_bp = Blueprint('breaks', __name__, url_prefix='/api/breaks')


@breaks_bp.route('', methods=['GET'])
def get_breaks():
    db = get_db()
    query = 'SELECT * FROM break_activities WHERE is_blocked = 0'
    params = []

    screen_free = request.args.get('screen_free')
    favorited   = request.args.get('favorited')
    custom      = request.args.get('custom')

    if screen_free is not None:
        query += ' AND is_screen_free = ?'
        params.append(int(screen_free))
    if favorited is not None:
        query += ' AND is_favorited = ?'
        params.append(int(favorited))
    if custom is not None:
        query += ' AND is_custom = ?'
        params.append(int(custom))

    return jsonify([dict(r) for r in db.execute(query, params).fetchall()])


@breaks_bp.route('/blocked', methods=['GET'])
def get_blocked_breaks():
    db = get_db()
    rows = db.execute('SELECT * FROM break_activities WHERE is_blocked = 1').fetchall()
    return jsonify([dict(r) for r in rows])


@breaks_bp.route('', methods=['POST'])
def create_break():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    db = get_db()
    cursor = db.execute(
        '''INSERT INTO break_activities (name, description, category, duration_minutes, is_screen_free, is_custom)
           VALUES (?, ?, ?, ?, ?, 1)''',
        (data['name'], data.get('description'), data.get('category'),
         data.get('duration_minutes'), data.get('is_screen_free', 1))
    )
    db.commit()
    row = db.execute('SELECT * FROM break_activities WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@breaks_bp.route('/<int:break_id>/favorite', methods=['PUT'])
def toggle_favorite(break_id):
    db = get_db()
    row = db.execute('SELECT * FROM break_activities WHERE id = ?', (break_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Break activity not found'}), 404
    new_val = 0 if row['is_favorited'] else 1
    db.execute('UPDATE break_activities SET is_favorited = ? WHERE id = ?', (new_val, break_id))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM break_activities WHERE id = ?', (break_id,)).fetchone()))


@breaks_bp.route('/<int:break_id>/block', methods=['PUT'])
def toggle_block(break_id):
    db = get_db()
    row = db.execute('SELECT * FROM break_activities WHERE id = ?', (break_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Break activity not found'}), 404
    new_val = 0 if row['is_blocked'] else 1
    # Also clear favorite when blocking
    db.execute('UPDATE break_activities SET is_blocked = ?, is_favorited = 0 WHERE id = ?',
               (new_val, break_id))
    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM break_activities WHERE id = ?', (break_id,)).fetchone()))


@breaks_bp.route('/action-by-name', methods=['POST'])
def action_by_name():
    """Find or create a break activity by name and apply a favorite or block action.
    Used by the suggestion card, which may show AI-generated activities not yet in the DB."""
    data = request.get_json()
    if not data or not data.get('name') or data.get('action') not in ('favorite', 'block'):
        return jsonify({'error': 'name and action (favorite|block) are required'}), 400

    name   = data['name'].strip()
    action = data['action']
    db     = get_db()

    row = db.execute(
        'SELECT * FROM break_activities WHERE LOWER(name) = LOWER(?)', (name,)
    ).fetchone()

    if row is None:
        cursor = db.execute(
            '''INSERT INTO break_activities (name, description, category, duration_minutes, is_screen_free, is_custom)
               VALUES (?, ?, ?, ?, 1, 0)''',
            (name, data.get('description'), data.get('category'), data.get('duration_minutes'))
        )
        db.commit()
        row = db.execute('SELECT * FROM break_activities WHERE id = ?', (cursor.lastrowid,)).fetchone()

    if action == 'favorite':
        new_fav = 0 if row['is_favorited'] else 1
        db.execute('UPDATE break_activities SET is_favorited = ?, is_blocked = 0 WHERE id = ?',
                   (new_fav, row['id']))
    else:  # block
        new_blocked = 0 if row['is_blocked'] else 1
        db.execute('UPDATE break_activities SET is_blocked = ?, is_favorited = 0 WHERE id = ?',
                   (new_blocked, row['id']))

    db.commit()
    return jsonify(dict(db.execute('SELECT * FROM break_activities WHERE id = ?', (row['id'],)).fetchone()))


@breaks_bp.route('/<int:break_id>', methods=['DELETE'])
def delete_break(break_id):
    db = get_db()
    row = db.execute('SELECT * FROM break_activities WHERE id = ?', (break_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Break activity not found'}), 404
    if not row['is_custom']:
        return jsonify({'error': 'Cannot delete built-in activities — use block instead'}), 403
    db.execute('DELETE FROM break_activities WHERE id = ?', (break_id,))
    db.commit()
    return '', 204
