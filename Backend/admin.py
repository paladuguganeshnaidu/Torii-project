from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from .db_adapter import get_db_connection
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin password hash - set via ADMIN_PASSWORD environment variable
# Default password is "admin123" - CHANGE THIS IMMEDIATELY!
# Generate new hash: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourPassword'))"
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD', 'pbkdf2:sha256:600000$8c6976e5b5410415$bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918')

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
