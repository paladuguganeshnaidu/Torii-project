from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from werkzeug.security import check_password_hash, generate_password_hash
from .db_adapter import get_db_connection
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

"""Admin authentication configuration.

You should set ADMIN_PASSWORD as a hashed value (output of generate_password_hash).
For convenience, if ADMIN_PASSWORD looks like plaintext (no known hash scheme
prefix), we'll hash it at startup. Default is a strong hash for 'admin123'.
"""

_DEFAULT_HASH = (
    'scrypt:32768:8:1$xgInVDOssyMWNUsh$161cba3e03e41893ab4c85979d6d146d599a793972152731e'
    'ed1b28108a08553429604eb00e6c979914b0d211198ef75d774924d298e2d156c754d69345b9e90'
)

_env_val = os.getenv('ADMIN_PASSWORD')
if not _env_val:
    ADMIN_PASSWORD_HASH = _DEFAULT_HASH
else:
    # If it already looks like a Werkzeug hash (has a scheme prefix like pbkdf2: or scrypt:), use as-is
    if any(_env_val.startswith(prefix) for prefix in ('pbkdf2:', 'scrypt:', 'argon2:', 'sha256:', 'sha1:')):
        ADMIN_PASSWORD_HASH = _env_val
    else:
        # Treat as plaintext and hash it so check_password_hash works
        ADMIN_PASSWORD_HASH = generate_password_hash(_env_val)

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Check password securely
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_authenticated'] = True
            flash('Admin login successful', 'success')
            return redirect(url_for('admin.view_users'))
        else:
            flash('Invalid admin password', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_authenticated', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@admin_bp.route('/users')
def view_users():
    """View all registered users (admin only)."""
    # Check if admin is authenticated
    if not session.get('admin_authenticated'):
        flash('Please login as admin first', 'error')
        return redirect(url_for('admin.admin_login'))
    
    conn = get_db_connection()
    
    try:
        # Safe SQL query - no user input involved, protected against SQL injection
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, email, mobile, registered_at 
            FROM users 
            ORDER BY registered_at DESC
        ''')
        users = cursor.fetchall()
        
        # Debug logging
        print(f"[ADMIN DEBUG] Found {len(users)} users in database")
        for user in users:
            print(f"[ADMIN DEBUG] User: {user}")
            
    except Exception as e:
        print(f"[ADMIN ERROR] Failed to fetch users: {e}")
        users = []
    finally:
        conn.close()
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/debug-db')
def debug_db():
    """Debug endpoint to check database state (admin only)."""
    from flask import jsonify
    import os
    
    # Check if admin is authenticated
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized - Please login as admin'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get database file path
        from .config import Config
        db_path = Config.DATABASE
        
        # Check if using SQLite or MySQL
        mysql_host = os.getenv('MYSQL_HOST')
        db_type = "MySQL" if mysql_host else "SQLite"
        
        # Get all tables
        if db_type == "SQLite":
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        else:
            cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # Get all users
        cursor.execute('SELECT id, email, mobile, registered_at FROM users ORDER BY registered_at DESC')
        users = cursor.fetchall()
        
        # Get user count
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        return jsonify({
            'database_type': db_type,
            'database_path': db_path if db_type == "SQLite" else mysql_host,
            'database_exists': os.path.exists(db_path) if db_type == "SQLite" else True,
            'tables': [t[0] for t in tables],
            'user_count': user_count,
            'users': [
                {
                    'id': u[0],
                    'email': u[1],
                    'mobile': u[2],
                    'registered_at': str(u[3])
                }
                for u in users
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
