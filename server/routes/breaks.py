from flask import Blueprint, request, jsonify
from server.database import get_db

breaks_bp = Blueprint('breaks', __name__, url_prefix='/api/breaks')


@breaks_bp.route('', methods=['GET'])
def get_breaks():
    db = get_db()
    query = 'SELECT * FROM break_activities WHERE 1=1'
    params = []

    screen_free = request.args.get('screen_free')
    favorited   = request.args.get('favorited')

    if screen_free is not None:
        query += ' AND is_screen_free = ?'
        params.append(int(screen_free))
    if favorited is not None:
        query += ' AND is_favorited = ?'
        params.append(int(favorited))

    return jsonify([dict(r) for r in db.execute(query, params).fetchall()])


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


@breaks_bp.route('/<int:break_id>', methods=['DELETE'])
def delete_break(break_id):
    db = get_db()
    row = db.execute('SELECT * FROM break_activities WHERE id = ?', (break_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'Break activity not found'}), 404
    if not row['is_custom']:
        return jsonify({'error': 'Cannot delete default break activities'}), 403
    db.execute('DELETE FROM break_activities WHERE id = ?', (break_id,))
    db.commit()
    return '', 204
