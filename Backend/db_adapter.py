"""
Unified database adapter that supports PostgreSQL, MySQL, and SQLite.
- Uses PostgreSQL if DATABASE_URL is configured (Render production)
- Uses MySQL if MYSQL_HOST is configured (local development with Workbench)
- Falls back to SQLite if no config (basic local development)
"""
import os
import sqlite3
from flask import g

# Try to import PostgreSQL support
try:
    import importlib
    psycopg2 = importlib.import_module('psycopg2')
    try:
        PgDictCursor = importlib.import_module('psycopg2.extras').DictCursor
    except Exception:
        PgDictCursor = None
    POSTGRES_AVAILABLE = True
except Exception:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    PgDictCursor = None

# Try to import MySQL support
try:
    # Import dynamically to avoid linter/IDE import resolution errors when the
    # optional dependency isn't installed in every environment.
    import importlib
    pymysql = importlib.import_module('pymysql')
    try:
        DictCursor = importlib.import_module('pymysql.cursors').DictCursor
    except Exception:
        DictCursor = None
    MYSQL_AVAILABLE = True
except Exception:
    MYSQL_AVAILABLE = False
    pymysql = None
    DictCursor = None


def get_db_connection():
    """
    Get a database connection.
    Priority: PostgreSQL > MySQL > SQLite
    """
    # Check if we already have a connection in this request
    if 'db_conn' in g:
        return g.db_conn
    
    # Try PostgreSQL first (for Render production)
    if POSTGRES_AVAILABLE and os.environ.get('DATABASE_URL'):
        conn = _get_postgres_connection()
        if conn:
            g.db_conn = conn
            g.db_type = 'postgres'
            return conn
    
    # Try MySQL second (for local development)
    if MYSQL_AVAILABLE and os.environ.get('MYSQL_HOST'):
        conn = _get_mysql_connection()
        if conn:
            g.db_conn = conn
            g.db_type = 'mysql'
            return conn
    
    # Fall back to SQLite (basic local dev)
    conn = _get_sqlite_connection()
    g.db_conn = conn
    g.db_type = 'sqlite'
    return conn


def _get_postgres_connection():
    """Get PostgreSQL connection if configured."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        # Render uses postgres:// but psycopg2 needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transactions
        print("[DB] Connected to PostgreSQL")
        return conn
    except Exception as e:
        print(f"[DB] PostgreSQL connection failed: {e}")
        return None


def _get_mysql_connection():
    """Get MySQL connection if configured."""
    try:
        ssl_enabled = os.getenv('MYSQL_USE_SSL', 'false').lower() == 'true'
        
        connection_params = {
            'host': os.environ.get('MYSQL_HOST'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER'),
            'password': os.environ.get('MYSQL_PASSWORD'),
            'database': os.environ.get('MYSQL_DB'),
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': False
        }
        
        if ssl_enabled:
            connection_params['ssl'] = {'ssl_mode': 'REQUIRED'}
        
        return pymysql.connect(**connection_params)
    except Exception:
        return None


def _get_sqlite_connection():
    """Get SQLite connection."""
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'app.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    return conn


def close_db_connection(e=None):
    """Close the database connection."""
    conn = g.pop('db_conn', None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def init_database(app):
    """Initialize database tables for PostgreSQL, MySQL, or SQLite."""
    # Determine which database we're using
    using_postgres = POSTGRES_AVAILABLE and os.environ.get('DATABASE_URL')
    using_mysql = MYSQL_AVAILABLE and os.environ.get('MYSQL_HOST')
    
    if using_postgres:
        _init_postgres_tables(app)
    elif using_mysql:
        _init_mysql_tables(app)
    else:
        _init_sqlite_tables(app)


def _init_postgres_tables(app):
    """Create PostgreSQL tables."""
    try:
        conn = _get_postgres_connection()
        if not conn:
            app.logger.info('PostgreSQL not configured; skipping Postgres init')
            return
        
        with conn.cursor() as cur:
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    mobile VARCHAR(20),
                    password_hash VARCHAR(255) NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Case-insensitive unique constraint on email
            try:
                cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_ci ON users (LOWER(email))")
            except Exception:
                pass
            
            # Tool logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tool_logs (
                    id SERIAL PRIMARY KEY,
                    tool_name VARCHAR(100),
                    input TEXT,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            try:
                cur.execute("CREATE INDEX IF NOT EXISTS idx_tool_logs_created_at ON tool_logs(created_at)")
            except Exception:
                pass
            
            conn.commit()
            app.logger.info('PostgreSQL tables initialized successfully')
        
        conn.close()
    except Exception as e:
        app.logger.warning(f'PostgreSQL table init failed: {e}')
        import traceback
        traceback.print_exc()


def _init_mysql_tables(app):
    """Create MySQL tables."""
    try:
        conn = _get_mysql_connection()
        if not conn:
            app.logger.info('MySQL not configured; skipping MySQL init')
            return
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    mobile VARCHAR(20) NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # Add generated column for case-insensitive unique constraint
            try:
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_ci VARCHAR(255) GENERATED ALWAYS AS (LOWER(email)) STORED")
            except Exception:
                pass
            # Create unique index on generated column
            try:
                cur.execute("CREATE UNIQUE INDEX idx_email_ci ON users (email_ci)")
            except Exception:
                pass
        conn.commit()
        conn.close()
        app.logger.info('✅ MySQL database initialized')
    except Exception as e:
        app.logger.warning(f'MySQL init failed: {e}')


def _init_sqlite_tables(app):
    """Create SQLite tables."""
    try:
        conn = _get_sqlite_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                mobile TEXT,
                password_hash TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON users(email)")
        # Case-insensitive unique email index using expression index
        try:
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_ci ON users(lower(email))")
        except Exception:
            pass
        conn.commit()
        conn.close()
        app.logger.info('✅ SQLite database initialized')
    except Exception as e:
        app.logger.warning(f'SQLite init failed: {e}')


def insert_user(email, mobile, password_hash):
    """
    Insert a new user into the database.
    Works with PostgreSQL, MySQL, and SQLite.
    """
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')
    
    try:
        if db_type == 'postgres':
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, mobile, password_hash) VALUES (%s, %s, %s)",
                    (email, mobile, password_hash)
                )
            conn.commit()
        elif db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, mobile, password_hash) VALUES (%s, %s, %s)",
                    (email, mobile, password_hash)
                )
            conn.commit()
        else:  # sqlite
            conn.execute(
                "INSERT INTO users (email, mobile, password_hash) VALUES (?, ?, ?)",
                (email, mobile, password_hash)
            )
            conn.commit()
        return True
    except Exception as e:
        # Check for duplicate email
        error_msg = str(e).lower()
        if 'duplicate' in error_msg or 'unique' in error_msg:
            raise ValueError("Email is already registered")
        raise e


def get_user_by_email(email):
    """
    Get a user by email and return a consistent dictionary across DBs.
    Keys: id, email, password_hash, mobile, registered_at
    """
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')

    try:
        if db_type == 'postgres':
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, password_hash, mobile, registered_at FROM users WHERE LOWER(email) = %s",
                    (email.lower(),)
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    'id': row[0],
                    'email': row[1],
                    'password_hash': row[2],
                    'mobile': row[3],
                    'registered_at': str(row[4]) if len(row) > 4 else None,
                }
        elif db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, password_hash, mobile, registered_at FROM users WHERE LOWER(email) = %s",
                    (email.lower(),)
                )
                row = cur.fetchone()
                if not row:
                    return None
                if isinstance(row, dict):
                    return row
                return {
                    'id': row[0],
                    'email': row[1],
                    'password_hash': row[2],
                    'mobile': row[3],
                    'registered_at': str(row[4]) if len(row) > 4 else None,
                }
        else:  # sqlite
            cursor = conn.execute(
                "SELECT id, email, password_hash, mobile, registered_at FROM users WHERE LOWER(email) = ?",
                (email.lower(),)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except Exception:
        return None


def get_user_by_id(user_id):
    """
    Get a user by ID.
    Works with PostgreSQL, MySQL, and SQLite.
    """
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')
    
    try:
        if db_type == 'postgres':
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, mobile, registered_at FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    'id': row[0],
                    'email': row[1],
                    'mobile': row[2],
                    'registered_at': str(row[3])
                }
        elif db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, mobile, registered_at FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return None
                if isinstance(row, dict):
                    return row
                return {
                    'id': row[0],
                    'email': row[1],
                    'mobile': row[2],
                    'registered_at': str(row[3])
                }
        else:  # sqlite
            cursor = conn.execute("SELECT id, email, mobile, registered_at FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except Exception:
        return None


def update_user_password(user_id, new_password_hash):
    """
    Update user's password.
    Works with PostgreSQL, MySQL, and SQLite.
    """
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')
    
    try:
        if db_type == 'postgres':
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (new_password_hash, user_id)
                )
            conn.commit()
        elif db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (new_password_hash, user_id)
                )
            conn.commit()
        else:  # sqlite
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user_id)
            )
            conn.commit()
        return True
    except Exception:
        return False
