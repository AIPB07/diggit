import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        # reached via user submitting registration form
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(buffered=True)
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        else:
            cursor.execute(
            "SELECT id FROM user WHERE username = %s", (username,)
            )
            if cursor.fetchone() is not None:
                error = f'The username {username} is already taken'
        
        if error is None:
            cursor.execute(
                "INSERT INTO user (username, password) VALUES (%s, %s)",
            (username, generate_password_hash(password)))
            db.commit()
            cursor.close()
            return redirect(url_for('auth.login'))

        cursor.close()
        flash(error)
    
    # reached via clicking a link
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        # reached via user submitting login form
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(buffered=True)
        error = None
        cursor.execute(
            "SELECT * FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            error = 'Incorrect username'
        elif not check_password_hash(user[2], password):
            error = 'Incorrect password'
        
        if error is None:
            session.clear()
            session['user_id'] = user[0]
            cursor.close()
            return redirect(url_for('shelf.index'))

        cursor.close()
        flash(error)

    # reached via clicking a link
    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "SELECT * FROM user WHERE id = %s", (user_id,)
        )
        g.user = cursor.fetchone()
        cursor.close()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view
