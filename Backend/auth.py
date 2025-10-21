from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from .mysql_db import get_mysql

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        mobile = (request.form.get('mobile') or '').strip()
        password = request.form.get('password') or ''
        confirm = request.form.get('confirm') or ''

        # basic validation
        errors = []
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password and len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html', email=email, mobile=mobile)

        # persist to MySQL
        conn = get_mysql()
        if conn is None:
            flash('Registration database is not configured. Please set up MySQL.', 'error')
            return render_template('register.html', email=email, mobile=mobile)
        try:
            pwd_hash = generate_password_hash(password)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (email, mobile, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (email, mobile or None, pwd_hash),
                )
            conn.commit()
        except Exception as e:
            # duplicate email or other DB error
            msg = str(e)
            if 'Duplicate' in msg or 'UNIQUE' in msg:
                flash('Email is already registered.', 'error')
            else:
                flash(f'Registration failed: {e}', 'error')
            return render_template('register.html', email=email, mobile=mobile)

        # store session and redirect
        session['user'] = email
        flash('Registered successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Skeleton: accepts any username/password
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')
        session['user'] = username
        flash('Logged in successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out.', 'info')
    return redirect(url_for('index'))
