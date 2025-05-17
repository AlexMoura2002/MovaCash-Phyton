from flask import render_template, request, redirect, url_for, session
from app import app
from app.models import verificar_usuario

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['password']

    usuario = verificar_usuario(email, senha)
    if usuario:
        session['usuario'] = usuario['nome']
        return redirect(url_for('dashboard'))
    else:
        return 'Login inválido!'

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('home'))
    return f'Bem-vindo, {session["usuario"]}! Esta é a área protegida.'

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('home'))
