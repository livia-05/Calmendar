import sqlite3
import os
from flask import g, current_app

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'calmendar.db')
SCHEMA   = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')


def _db_path():
    try:
        return current_app.config.get('DATABASE', DATABASE)
    except RuntimeError:
        return DATABASE


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config.get('DATABASE', DATABASE))
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    path = _db_path()
    db = sqlite3.connect(path)
    with open(SCHEMA) as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def _migrate(app):
    """Add columns that were introduced after the initial schema."""
    with app.app_context():
        db = get_db()
        existing = {row[1] for row in db.execute('PRAGMA table_info(break_activities)').fetchall()}
        if 'is_blocked' not in existing:
            db.execute('ALTER TABLE break_activities ADD COLUMN is_blocked INTEGER DEFAULT 0')
            db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    _migrate(app)


if __name__ == '__main__':
    init_db()
    print(f'Database initialized at {DATABASE}')
