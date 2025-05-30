from flask import render_template, request, redirect, url_for, session
from app import db
from app.models import Usuario, Movimentacao, Conta
from app.utils import login_obrigatorio
from flask import current_app as app
from datetime import datetime

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email, senha=senha).first()
        if usuario:
            session['usuario_id'] = usuario.id
            session['usuario_email'] = usuario.email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', erro='Credenciais inválidas')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        novo_usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_obrigatorio
def dashboard():
    usuario_id = session.get('usuario_id')
    usuario = session.get('usuario_email')

    if request.method == 'POST':
        tipo = request.form['tipo']
        categoria = request.form['categoria']
        valor = float(request.form['valor'])
        data_str = request.form['data']
        data = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else datetime.now().date()

        nova = Movimentacao(tipo=tipo, categoria=categoria, valor=valor, data=data, usuario_id=usuario_id)
        db.session.add(nova)
        db.session.commit()
        return redirect(url_for('dashboard'))

    movimentacoes = Movimentacao.query.filter_by(usuario_id=usuario_id).order_by(Movimentacao.data.desc()).all()
    saldo = sum(m.valor if m.tipo == 'receita' else -m.valor for m in movimentacoes)

    dados = [(m.tipo, m.categoria, m.valor, m.data.strftime('%d/%m/%Y'), m.id) for m in movimentacoes]

    return render_template('dashboard.html', usuario=usuario, saldo=saldo, movimentacoes=dados)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_movimentacao(id):
    mov = Movimentacao.query.get_or_404(id)

    if request.method == 'POST':
        mov.tipo = request.form['tipo']
        mov.categoria = request.form['categoria']
        mov.valor = float(request.form['valor'])
        data_str = request.form['data']
        mov.data = datetime.strptime(data_str, '%Y-%m-%d').date()
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('editar.html', mov=mov)

@app.route('/excluir/<int:id>')
@login_obrigatorio
def excluir_movimentacao(id):
    mov = Movimentacao.query.get_or_404(id)
    db.session.delete(mov)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/contas', methods=['GET', 'POST'])
@login_obrigatorio
def contas():
    usuario_id = session.get('usuario_id')

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        vencimento_str = request.form['vencimento']
        vencimento = datetime.strptime(vencimento_str, '%Y-%m-%d').date()
        status = request.form['status']

        nova_conta = Conta(
            descricao=descricao,
            valor=valor,
            vencimento=vencimento,
            status=status,
            usuario_id=usuario_id
        )
        db.session.add(nova_conta)
        db.session.commit()
        return redirect(url_for('contas'))

    status_filtro = request.args.get('status')
    if status_filtro:
        contas = Conta.query.filter_by(usuario_id=usuario_id, status=status_filtro).order_by(Conta.vencimento).all()
    else:
        contas = Conta.query.filter_by(usuario_id=usuario_id).order_by(Conta.vencimento).all()

    return render_template('contas.html', contas=contas)

@app.route('/editar_conta/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_conta(id):
    conta = Conta.query.get_or_404(id)

    if request.method == 'POST':
        conta.descricao = request.form['descricao']
        conta.valor = float(request.form['valor'])
        vencimento_str = request.form['vencimento']
        conta.vencimento = datetime.strptime(vencimento_str, '%Y-%m-%d').date()
        conta.status = request.form['status']
        db.session.commit()
        return redirect(url_for('contas'))

    return render_template('editar_conta.html', conta=conta)

@app.route('/excluir_conta/<int:id>')
@login_obrigatorio
def excluir_conta(id):
    conta = Conta.query.get_or_404(id)
    db.session.delete(conta)
    db.session.commit()
    return redirect(url_for('contas'))
