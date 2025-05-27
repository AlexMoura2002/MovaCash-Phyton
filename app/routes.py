from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import verificar_login, criar_usuario, verificar_usuario_existente, adicionar_movimentacao, obter_movimentacoes
from datetime import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return render_template('login.html')

@routes.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']

    if verificar_login(email, senha):
        session['usuario'] = email
        return redirect(url_for('routes.dashboard'))
    else:
        return render_template('login.html', erro='Login inválido')

@routes.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('routes.home'))

@routes.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if verificar_usuario_existente(email):
            return render_template('cadastro.html', erro='Usuário já existe.')

        criar_usuario(nome, email, senha)
        return redirect(url_for('routes.home'))

    return render_template('cadastro.html')

@routes.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('routes.home'))

    email = session['usuario']

    if request.method == 'POST':
        tipo = request.form['tipo']
        categoria = request.form['categoria']
        valor = float(request.form['valor'])
        data = request.form['data'] or datetime.today().strftime('%Y-%m-%d')

        adicionar_movimentacao(email, tipo, categoria, valor, data)

    movimentacoes = obter_movimentacoes(email)
    saldo = 0
    for mov in movimentacoes:
        if mov[0] == 'receita':
            saldo += mov[2]
        else:
            saldo -= mov[2]

    return render_template('dashboard.html', usuario=email, movimentacoes=movimentacoes, saldo=saldo)
