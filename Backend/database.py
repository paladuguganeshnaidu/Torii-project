import os
import sqlite3
from flask import g
from .config import DB_DIR, DB_PATH, SCHEMA_PATH


def ensure_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


def get_db():
    if 'db' not in g:
        ensure_db_dir()
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app=None):
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    if app:
        app.logger.info('Database initialized at %s', DB_PATH)
