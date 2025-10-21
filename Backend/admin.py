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
    finally:
        conn.close()
    
    return render_template('admin/users.html', users=users)
