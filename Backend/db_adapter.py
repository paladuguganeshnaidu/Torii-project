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
    import psycopg2
    from psycopg2.extras import DictCursor as PgDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    PgDictCursor = None

# Try to import MySQL support
try:
    import pymysql
    from pymysql.cursors import DictCursor
    MYSQL_AVAILABLE = True
except ImportError:
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
    Get a user by email.
    Works with PostgreSQL, MySQL, and SQLite.
    """
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')
    
    try:
        if db_type == 'postgres':
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                return cur.fetchone()
        elif db_type == 'mysql':
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                return cur.fetchone()
        else:  # sqlite
            cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except Exception:
        return None
