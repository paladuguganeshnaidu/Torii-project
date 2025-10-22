from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .db_adapter import insert_user, get_db_connection, get_user_by_email

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

        # persist to database (MySQL or SQLite)
        try:
            pwd_hash = generate_password_hash(password)
            insert_user(email, mobile or None, pwd_hash)
        except ValueError as e:
            # Duplicate email
            flash(str(e), 'error')
            return render_template('register.html', email=email, mobile=mobile)
        except Exception as e:
            flash(f'Registration failed: {e}', 'error')
            return render_template('register.html', email=email, mobile=mobile)

        # store session and redirect
        session['user'] = email
        flash('Registered successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with proper password validation."""
    if request.method == 'POST':
        email = (request.form.get('email') or request.form.get('username') or '').strip().lower()
        password = request.form.get('password') or ''
        
        # Validate input
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('login.html')
        
        try:
            # Get user by email using DB-agnostic adapter (now returns dict)
            user = get_user_by_email(email)

            if not user:
                # User not found
                flash('Invalid email or password.', 'error')
                print(f"[LOGIN] User not found: {email}")
                return render_template('login.html')

            # Extract user data (dict expected; tuple fallback retained just in case)
            if isinstance(user, dict):
                user_id = user.get('id')
                user_email = user.get('email')
                password_hash = user.get('password_hash')
            else:
                # Fallback for legacy tuple return
                user_id = user[0]
                user_email = user[1]
                # Most schemas: id, email, password_hash, mobile, registered_at
                password_hash = user[2] if len(user) > 2 else None
            
            # Verify password using Werkzeug's secure hash comparison
            if check_password_hash(password_hash, password):
                # Password correct - create session
                session['user_id'] = user_id
                session['user'] = user_email
                flash('Logged in successfully!', 'success')
                print(f"[LOGIN] Success: {user_email}")
                return redirect(url_for('index'))
            else:
                # Password wrong
                flash('Invalid email or password.', 'error')
                print(f"[LOGIN] Invalid password for: {user_email}")
                return render_template('login.html')
                
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
            print(f"[LOGIN ERROR] {str(e)}")
            return render_template('login.html')
        finally:
            pass
    
    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Logout user and clear session."""
    session.clear()  # Clear all session data
    return redirect(url_for('index'))
