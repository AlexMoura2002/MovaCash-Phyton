from functools import wraps
from flask import session, redirect, url_for

def login_obrigatorio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_obrigatorio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('usuario_tipo') != 'admin':
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function