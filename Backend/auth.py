from flask import Blueprint, render_template, request, redirect, url_for, session, flash

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Skeleton: no DB persistence yet
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')
        # In a real app: hash password and store user to DB
        session['user'] = username
        flash('Registered and logged in.', 'success')
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
