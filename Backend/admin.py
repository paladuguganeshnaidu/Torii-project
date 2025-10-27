from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from .db_adapter import get_db_connection
from flask import g
import os
import time

# DoS detection tools (detector removed)
# DoSDetector removed — keep analyzer/mitigator for other admin capabilities
from .tools.analyzer import Analyzer
from .tools.mitigator import Mitigator

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Initialize admin helpers. Detector is not available in this deployment.
detector = None
analyzer = Analyzer()
mitigator = Mitigator()

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
    # Check if admin is authenticated
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized - Please login as admin'}), 401
    
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')
    
    try:
        # Get database info
        database_url = os.getenv('DATABASE_URL')
        mysql_host = os.getenv('MYSQL_HOST')
        
        # Get all tables
        cursor = conn.cursor()
        if db_type == "postgres":
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        elif db_type == "mysql":
            cursor.execute("SHOW TABLES")
        else:  # sqlite
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # Get all users
        cursor.execute('SELECT id, email, mobile, registered_at FROM users ORDER BY registered_at DESC')
        users = cursor.fetchall()
        
        # Get user count
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0] if cursor.fetchone() else 0
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        return jsonify({
            'database_type': db_type.upper(),
            'database_url_set': bool(database_url),
            'mysql_host_set': bool(mysql_host),
            'tables': [t[0] for t in tables],
            'user_count': user_count,
            'users': [
                {
                    'id': u[0] if not isinstance(u, dict) else u.get('id'),
                    'email': u[1] if not isinstance(u, dict) else u.get('email'),
                    'mobile': u[2] if not isinstance(u, dict) else u.get('mobile'),
                    'registered_at': str(u[3]) if not isinstance(u, dict) else str(u.get('registered_at'))
                }
                for u in users
            ],
            'warning': 'SQLite data is temporary on Render free tier!' if db_type == 'sqlite' else None
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        conn.close()


@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with database monitoring."""
    if not session.get('admin_authenticated'):
        flash('Please login as admin first', 'error')
        return redirect(url_for('admin.admin_login'))
    
    return render_template('admin/dashboard.html')


@admin_bp.route('/api/db-stats')
def api_db_stats():
    """API endpoint for database statistics."""
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    db_type = g.get('db_type', 'sqlite')
    
    try:
        cursor = conn.cursor()
        
        # Get user count
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # Get tool logs count
        try:
            cursor.execute('SELECT COUNT(*) FROM tool_logs')
            log_count = cursor.fetchone()[0]
        except:
            log_count = 0
        
        # Get recent registrations (last 7 days)
        if db_type == 'postgres':
            cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at > NOW() - INTERVAL '7 days'")
        elif db_type == 'mysql':
            cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at > DATE_SUB(NOW(), INTERVAL 7 DAY)")
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at > datetime('now', '-7 days')")
        recent_users = cursor.fetchone()[0]
        
        # Estimate database size
        avg_user_size = 300  # bytes
        avg_log_size = 2000  # bytes
        estimated_size_bytes = (user_count * avg_user_size) + (log_count * avg_log_size)
        estimated_size_mb = estimated_size_bytes / (1024 * 1024)
        
        # Calculate storage percentage (800 MB limit)
        storage_limit_mb = 800
        storage_percentage = (estimated_size_mb / storage_limit_mb) * 100
        
        # Get oldest log date
        try:
            cursor.execute('SELECT MIN(created_at) FROM tool_logs')
            oldest_log = cursor.fetchone()[0]
            oldest_log_str = str(oldest_log) if oldest_log else None
        except:
            oldest_log_str = None
        
        return jsonify({
            'ok': True,
            'db_type': db_type.upper(),
            'user_count': user_count,
            'log_count': log_count,
            'recent_users': recent_users,
            'estimated_size_mb': round(estimated_size_mb, 2),
            'storage_limit_mb': storage_limit_mb,
            'storage_percentage': round(storage_percentage, 1),
            'oldest_log': oldest_log_str,
            'warnings': []
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        conn.close()


@admin_bp.route('/api/incidents', methods=['GET'])
def get_incidents():
    # Admin auth check
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401

    # Collect analyzer/mitigator state
    try:
        global_spike = analyzer.detect_global_spike()
        high_rate_ips = analyzer.detect_per_ip_flood()
        z_alerts = [ip for ip in analyzer.ip_requests if analyzer.calculate_z_score(ip) > 3]
        blocked = list(mitigator.blocked_ips.keys())

        return jsonify({
            'global_spike': global_spike,
            'high_traffic_ips': high_rate_ips,
            'anomalous_ips': z_alerts,
            'blocked_ips': blocked,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
