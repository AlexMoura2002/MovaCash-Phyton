from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from .models import Usuario, Movimentacao, Conta
from . import db
from .utils import login_obrigatorio
from datetime import datetime, date
import pandas as pd
from io import BytesIO

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email, senha=senha).first()
        if usuario:
            session['usuario_id'] = usuario.id
            return redirect(url_for('main.dashboard'))
        return 'Credenciais inválidas'
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('cadastro.html')

@bp.route('/dashboard', methods=['GET', 'POST'])
@login_obrigatorio
def dashboard():
    usuario_id = session['usuario_id']
    usuario = Usuario.query.get(usuario_id).nome

    if request.method == 'POST':
        tipo = request.form['tipo']
        categoria = request.form['categoria']
        valor = float(request.form['valor'])
        data_str = request.form['data']
        data = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else date.today()

        nova = Movimentacao(tipo=tipo, categoria=categoria, valor=valor, data=data, usuario_id=usuario_id)
        db.session.add(nova)
        db.session.commit()

    movimentacoes = Movimentacao.query.filter_by(usuario_id=usuario_id).order_by(Movimentacao.data.desc()).all()
    saldo = sum(m.valor if m.tipo == 'receita' else -m.valor for m in movimentacoes)
    mov_list = [(m.tipo, m.categoria, m.valor, m.data, m.id) for m in movimentacoes]

    return render_template('dashboard.html', usuario=usuario, saldo=saldo, movimentacoes=mov_list)

@bp.route('/excluir/<int:id>')
@login_obrigatorio
def excluir_movimentacao(id):
    movimentacao = Movimentacao.query.get(id)
    db.session.delete(movimentacao)
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@bp.route('/contas', methods=['GET', 'POST'])
@login_obrigatorio
def contas():
    usuario_id = session['usuario_id']
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        vencimento_str = request.form['vencimento']
        vencimento = datetime.strptime(vencimento_str, '%Y-%m-%d').date()
        status = request.form['status']

        nova_conta = Conta(descricao=descricao, valor=valor, vencimento=vencimento, status=status, usuario_id=usuario_id)
        db.session.add(nova_conta)
        db.session.commit()

    status_filtro = request.args.get('status')
    if status_filtro:
        contas = Conta.query.filter_by(usuario_id=usuario_id, status=status_filtro).order_by(Conta.vencimento).all()
    else:
        contas = Conta.query.filter_by(usuario_id=usuario_id).order_by(Conta.vencimento).all()

    return render_template('contas.html', contas=contas)

@bp.route('/editar-conta/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_conta(id):
    conta = Conta.query.get(id)
    if request.method == 'POST':
        conta.descricao = request.form['descricao']
        conta.valor = float(request.form['valor'])
        conta.vencimento = datetime.strptime(request.form['vencimento'], '%Y-%m-%d').date()
        conta.status = request.form['status']
        db.session.commit()
        return redirect(url_for('main.contas'))
    return render_template('editar_conta.html', conta=conta)

@bp.route('/excluir-conta/<int:id>')
@login_obrigatorio
def excluir_conta(id):
    conta = Conta.query.get(id)
    db.session.delete(conta)
    db.session.commit()
    return redirect(url_for('main.contas'))

@bp.route('/relatorios', methods=['GET', 'POST'])
@login_obrigatorio
def relatorios():
    usuario_id = session['usuario_id']
    if request.method == 'POST':
        mes = int(request.form.get('mes'))
        ano = int(request.form.get('ano'))
    else:
        hoje = date.today()
        mes = hoje.month
        ano = hoje.year

    receitas = db.session.query(Movimentacao.categoria, db.func.sum(Movimentacao.valor))\
        .filter_by(usuario_id=usuario_id, tipo='receita')\
        .filter(db.extract('month', Movimentacao.data) == mes)\
        .filter(db.extract('year', Movimentacao.data) == ano)\
        .group_by(Movimentacao.categoria).all()

    despesas = db.session.query(Movimentacao.categoria, db.func.sum(Movimentacao.valor))\
        .filter_by(usuario_id=usuario_id, tipo='despesa')\
        .filter(db.extract('month', Movimentacao.data) == mes)\
        .filter(db.extract('year', Movimentacao.data) == ano)\
        .group_by(Movimentacao.categoria).all()

    return render_template('relatorios.html', receitas=receitas, despesas=despesas, mes=mes, ano=ano)

@bp.route('/exportar-excel')
@login_obrigatorio
def exportar_excel():
    usuario_id = session['usuario_id']
    movimentacoes = Movimentacao.query.filter_by(usuario_id=usuario_id).all()

    data = [
        {
            'Data': m.data.strftime('%d/%m/%Y'),
            'Tipo': m.tipo,
            'Categoria': m.categoria,
            'Valor': m.valor
        }
        for m in movimentacoes
    ]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Movimentacoes')

    output.seek(0)
    return send_file(output, download_name='movimentacoes.xlsx', as_attachment=True)

@bp.route('/editar-movimentacao/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_movimentacao(id):
    movimentacao = Movimentacao.query.get(id)
    if request.method == 'POST':
        movimentacao.tipo = request.form['tipo']
        movimentacao.categoria = request.form['categoria']
        movimentacao.valor = float(request.form['valor'])
        data_str = request.form['data']
        movimentacao.data = datetime.strptime(data_str, '%Y-%m-%d').date()
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('editar_movimentacao.html', m=movimentacao)
