import os
from flask import g

try:
    import pymysql
    from pymysql.cursors import DictCursor
except Exception:  # pragma: no cover - optional dependency until enabled
    pymysql = None
    DictCursor = None


def get_mysql_config(app=None):
    env = os.environ
    cfg = {
        'host': env.get('MYSQL_HOST') or (getattr(app, 'config', {}).get('MYSQL_HOST') if app else None),
        'user': env.get('MYSQL_USER') or (getattr(app, 'config', {}).get('MYSQL_USER') if app else None),
        'password': env.get('MYSQL_PASSWORD') or (getattr(app, 'config', {}).get('MYSQL_PASSWORD') if app else None),
        'database': env.get('MYSQL_DB') or (getattr(app, 'config', {}).get('MYSQL_DB') if app else None),
        'port': int(env.get('MYSQL_PORT') or (getattr(app, 'config', {}).get('MYSQL_PORT') or 3306)) if (env.get('MYSQL_PORT') or (getattr(app, 'config', {}).get('MYSQL_PORT') is not None)) else 3306,
    }
    # Minimal validity: require host, user, database
    if not cfg['host'] or not cfg['user'] or not cfg['database']:
        return None
    return cfg


def get_mysql():
    """Get or create a per-request MySQL connection if configured, else None."""
    if 'mysql' in g:
        return g.mysql
    if pymysql is None:
        return None
    cfg = get_mysql_config()
    if not cfg:
        return None
    conn = pymysql.connect(
        host=cfg['host'],
        user=cfg['user'],
        password=cfg['password'],
        database=cfg['database'],
        port=cfg['port'],
        cursorclass=DictCursor,
        autocommit=False,
        charset='utf8mb4',
    )
    g.mysql = conn
    return conn


def close_mysql(e=None):
    conn = g.pop('mysql', None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def init_mysql(app):
    """Create users table if MySQL is configured. No-op otherwise."""
    if pymysql is None:
        if app:
            app.logger.info('PyMySQL not installed; MySQL features disabled')
        return
    cfg = get_mysql_config(app)
    if not cfg:
        if app:
            app.logger.info('MySQL not configured; skipping MySQL init')
        return
    try:
        conn = pymysql.connect(
            host=cfg['host'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database'],
            port=cfg['port'],
            autocommit=True,
            charset='utf8mb4',
        )
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    mobile VARCHAR(20) NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        if app:
            app.logger.info('MySQL users table ensured')
    except Exception as e:
        if app:
            app.logger.warning(f'MySQL init failed: {e}')
