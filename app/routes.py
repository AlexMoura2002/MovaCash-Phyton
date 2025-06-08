from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, flash
from .models import Usuario, Movimentacao, Conta
from . import db
from .utils import login_obrigatorio
from datetime import datetime, date, timedelta
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func, extract, case

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
            usuario.ultimo_acesso = datetime.now()
            db.session.commit()
            session['usuario_id'] = usuario.id
            session['nome'] = usuario.nome
            session['tipo'] = usuario.tipo
            if usuario.tipo == 'admin':
                return redirect(url_for('main.dashboard'))
            else:
                return redirect(url_for('main.caixa'))
        flash('Credenciais inválidas', 'danger')
    return render_template('login.html')

@bp.route('/usuarios-logins')
@login_obrigatorio
def usuarios_logins():
    if session.get('tipo') != 'admin':
        return redirect(url_for('main.dashboard'))

    hoje = date.today()
    mes = request.args.get('mes', type=int) or hoje.month
    ano = request.args.get('ano', type=int) or hoje.year

    usuarios = Usuario.query.filter(
        Usuario.ultimo_acesso != None,
        extract('month', Usuario.ultimo_acesso) == mes,
        extract('year', Usuario.ultimo_acesso) == ano
    ).order_by(Usuario.ultimo_acesso.desc()).all()

    return render_template("usuarios_logins.html", usuarios=usuarios, mes=mes, ano=ano)

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
        usuario = Usuario(nome=nome, email=email, senha=senha, tipo='vendedor')
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('cadastro.html')

@bp.route('/dashboard')
@login_obrigatorio
def dashboard():
    usuario_id = session.get('usuario_id')
    nome_usuario = session.get('nome')

    hoje = date.today()
    filtro_data = request.args.get('filtro_data')
    mes = int(request.args.get('mes') or hoje.month)
    ano = int(request.args.get('ano') or hoje.year)

    # Consulta base
    query = Movimentacao.query.options(joinedload(Movimentacao.usuario)).filter(
        extract('month', Movimentacao.data) == mes,
        extract('year', Movimentacao.data) == ano
    )

    # Filtrar por usuário, se não for admin
    if session['tipo'] != 'admin':
        query = query.filter(Movimentacao.usuario_id == usuario_id)

    # Filtro por data específica
    if filtro_data:
        try:
            data_filtrada = datetime.strptime(filtro_data, '%Y-%m-%d').date()
            query = query.filter(Movimentacao.data == data_filtrada)
        except ValueError:
            flash('Data inválida', 'danger')

    movimentacoes = query.order_by(Movimentacao.data.desc()).all()

    mov_list = [
        (m.tipo, m.categoria, m.valor, m.data, m.id, m.usuario.nome if session['tipo'] == 'admin' else None)
        for m in movimentacoes
    ]

    # Totais do mês
    total_receitas = db.session.query(func.sum(Movimentacao.valor)).filter_by(tipo='receita').filter(
        extract('month', Movimentacao.data) == mes,
        extract('year', Movimentacao.data) == ano
    )
    total_despesas = db.session.query(func.sum(Movimentacao.valor)).filter_by(tipo='despesa').filter(
        extract('month', Movimentacao.data) == mes,
        extract('year', Movimentacao.data) == ano
    )

    if session['tipo'] != 'admin':
        total_receitas = total_receitas.filter(Movimentacao.usuario_id == usuario_id)
        total_despesas = total_despesas.filter(Movimentacao.usuario_id == usuario_id)

    receitas = total_receitas.scalar() or 0
    despesas = total_despesas.scalar() or 0
    saldo = receitas - despesas

    # 🚨 Buscar contas a vencer nos próximos 3 dias (somente admin)
    contas_proximas = None
    if session['tipo'] == 'admin':
        tres_dias = hoje + timedelta(days=3)
        contas_proximas = Conta.query.filter(
            Conta.vencimento <= tres_dias,
            Conta.vencimento >= hoje,
            Conta.status != 'paga'
        ).order_by(Conta.vencimento).all()

    return render_template(
        "dashboard.html",
        usuario=nome_usuario,
        saldo=saldo,
        total_receitas=receitas,
        total_despesas=despesas,
        movimentacoes=mov_list,
        filtro_data=filtro_data,
        mes=mes,
        ano=ano,
        contas_proximas=contas_proximas  # <- ⚠️ IMPORTANTE
    )

@bp.route('/cadastrar-usuario', methods=['GET', 'POST'])
@login_obrigatorio
def cadastrar_usuario():
    if session.get('tipo') != 'admin':
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']

        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
        else:
            novo = Usuario(nome=nome, email=email, senha=senha, tipo=tipo)
            db.session.add(novo)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('main.cadastrar_usuario'))

    usuarios = Usuario.query.all()
    return render_template('cadastrar_usuario.html', usuarios=usuarios)

@bp.route('/deletar-usuario/<int:id>', methods=['POST'])
@login_obrigatorio
def deletar_usuario(id):
    if session.get('tipo') != 'admin':
        return redirect(url_for('main.dashboard'))

    if id == session.get('usuario_id'):
        flash('Você não pode se excluir.', 'danger')
        return redirect(url_for('main.cadastrar_usuario'))

    usuario = Usuario.query.get(id)
    
    # Verificar se o usuário tem movimentações
    if Movimentacao.query.filter_by(usuario_id=id).first():
        flash('Não é possível excluir: este usuário possui movimentações registradas.', 'danger')
        return redirect(url_for('main.cadastrar_usuario'))

    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário deletado com sucesso.', 'success')
    return redirect(url_for('main.cadastrar_usuario'))

@bp.route('/editar-conta/<int:id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_conta(id):
    conta = Conta.query.get(id)

    if request.method == 'POST':
        conta.descricao = request.form['descricao']
        conta.valor = float(request.form['valor'])
        conta.vencimento = datetime.strptime(request.form['vencimento'], '%Y-%m-%d').date()
        novo_status = request.form['status']
        novo_tipo = request.form['tipo']

        # Se status mudou para "paga" e não estava assim antes
        if novo_status == 'paga' and conta.status != 'paga' and novo_tipo == 'pagar':
            # Evita criar duplicatas: verifica se já existe movimentação igual
            existe = Movimentacao.query.filter_by(
                tipo='despesa',
                categoria='Conta: ' + conta.descricao,
                valor=conta.valor,
                data=conta.vencimento,
                usuario_id=conta.usuario_id
            ).first()

            if not existe:
                despesa = Movimentacao(
                    tipo='despesa',
                    categoria='Conta: ' + conta.descricao,
                    valor=conta.valor,
                    data=conta.vencimento,
                    usuario_id=conta.usuario_id
                )
                db.session.add(despesa)

        conta.status = novo_status
        conta.tipo = novo_tipo
        db.session.commit()
        flash('Conta atualizada com sucesso.', 'success')
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
    tipo = session.get('tipo')
    hoje = date.today()
    mes = hoje.month
    ano = hoje.year

    if request.method == 'POST':
        mes = int(request.form.get('mes') or mes)
        ano = int(request.form.get('ano') or ano)
        vendedor_id = request.form.get('vendedor_id') if tipo == 'admin' else usuario_id
        categoria = request.form.get('categoria')
        valor_min = request.form.get('valor_min')
        valor_max = request.form.get('valor_max')
        data_inicial = request.form.get('data_inicial')
        data_final = request.form.get('data_final')
    else:
        vendedor_id = usuario_id
        categoria = valor_min = valor_max = data_inicial = data_final = None

    query = Movimentacao.query.filter(
        extract('month', Movimentacao.data) == mes,
        extract('year', Movimentacao.data) == ano
    )

    if vendedor_id:
        query = query.filter(Movimentacao.usuario_id == vendedor_id)
    if categoria:
        query = query.filter(Movimentacao.categoria == categoria)
    if valor_min:
        query = query.filter(Movimentacao.valor >= float(valor_min))
    if valor_max:
        query = query.filter(Movimentacao.valor <= float(valor_max))
    if data_inicial:
        query = query.filter(Movimentacao.data >= data_inicial)
    if data_final:
        query = query.filter(Movimentacao.data <= data_final)

    movimentos = query.all()

    receitas = db.session.query(
        Movimentacao.categoria,
        func.sum(Movimentacao.valor)
    ).filter_by(tipo='receita').filter(
        extract('month', Movimentacao.data) == mes,
        extract('year', Movimentacao.data) == ano
    )
    if vendedor_id:
        receitas = receitas.filter(Movimentacao.usuario_id == vendedor_id)
    receitas = receitas.group_by(Movimentacao.categoria).all()

    despesas = db.session.query(
        Movimentacao.categoria,
        func.sum(Movimentacao.valor)
    ).filter_by(tipo='despesa').filter(
        extract('month', Movimentacao.data) == mes,
        extract('year', Movimentacao.data) == ano
    )
    if vendedor_id:
        despesas = despesas.filter(Movimentacao.usuario_id == vendedor_id)
    despesas = despesas.group_by(Movimentacao.categoria).all()

    evolucao = db.session.query(
        extract('month', Movimentacao.data).label('mes'),
        func.sum(case((Movimentacao.tipo == 'receita', Movimentacao.valor), else_=0)).label('total_receitas'),
        func.sum(case((Movimentacao.tipo == 'despesa', Movimentacao.valor), else_=0)).label('total_despesas')
    ).filter(
        extract('year', Movimentacao.data) == ano
    )
    if vendedor_id:
        evolucao = evolucao.filter(Movimentacao.usuario_id == vendedor_id)
    evolucao = evolucao.group_by('mes').order_by('mes').all()

    receitas_json = [[r[0], float(r[1])] for r in receitas]
    despesas_json = [[d[0], float(d[1])] for d in despesas]
    evolucao_json = [
        {"mes": str(int(e.mes)).zfill(2), "total_receitas": float(e.total_receitas), "total_despesas": float(e.total_despesas)}
        for e in evolucao
    ]

    vendedores = Usuario.query.filter_by(tipo='vendedor').all() if tipo == 'admin' else []
    categorias = db.session.query(Movimentacao.categoria).distinct().all()

    return render_template("relatorios.html",
        tipo=tipo,
        vendedores=vendedores,
        categorias=categorias,
        receitas=receitas,
        despesas=despesas,
        receitas_json=receitas_json,
        despesas_json=despesas_json,
        evolucao_json=evolucao_json,
        mes=mes,
        ano=ano
    )

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

@bp.route('/contas', methods=['GET', 'POST'])
@login_obrigatorio
def contas():
    if session.get('tipo') != 'admin':
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        vencimento = datetime.strptime(request.form['vencimento'], '%Y-%m-%d').date()
        status = request.form['status']
        tipo = request.form.get('tipo')  # ✔️ seguro

        if not tipo:
            flash('Erro: o campo "tipo" é obrigatório.', 'danger')
            return redirect(url_for('main.contas'))

        nova_conta = Conta(
            descricao=descricao,
            valor=valor,
            vencimento=vencimento,
            status=status,
            tipo=tipo,
            usuario_id=session['usuario_id']
        )
        db.session.add(nova_conta)
        db.session.commit()
        flash('Conta cadastrada com sucesso!', 'success')
        return redirect(url_for('main.contas'))

    contas = Conta.query.order_by(Conta.vencimento).all()
    return render_template('contas.html', contas=contas)

@bp.route('/perfil', methods=['GET', 'POST'])
@login_obrigatorio
def perfil():
    usuario_id = session.get('usuario_id')
    usuario = Usuario.query.get(usuario_id)

    if request.method == 'POST':
        novo_nome = request.form['nome']
        novo_email = request.form['email']
        nova_senha = request.form['senha']

        # Verifica se o e-mail já existe para outro usuário
        existente = Usuario.query.filter(Usuario.email == novo_email, Usuario.id != usuario_id).first()
        if existente:
            flash('Este e-mail já está em uso por outro usuário.', 'danger')
        else:
            usuario.nome = novo_nome
            usuario.email = novo_email
            if nova_senha:
                usuario.senha = nova_senha
            db.session.commit()
            flash('Dados atualizados com sucesso!', 'success')
            session['nome'] = novo_nome  # Atualiza o nome na sessão também

    return render_template('perfil.html', usuario=usuario)

@bp.route('/movimentacoes/excluir/<int:id>', methods=['GET'])
@login_obrigatorio
def excluir_movimentacao(id):
    movimentacao = Movimentacao.query.get_or_404(id)

    # Verifica se o usuário pode excluir essa movimentação
    if session['tipo'] != 'admin' and movimentacao.usuario_id != session['usuario_id']:
        flash("Você não tem permissão para excluir essa movimentação.", "danger")
        return redirect(url_for('main.dashboard'))

    db.session.delete(movimentacao)
    db.session.commit()
    flash("Movimentação excluída com sucesso.", "success")
    return redirect(url_for('main.dashboard'))

@bp.route('/caixa', methods=['GET', 'POST'])
@login_obrigatorio
def caixa():
    if session.get('tipo') != 'vendedor':
        return redirect(url_for('main.dashboard'))

    usuario_id = session['usuario_id']
    hoje = date.today()
    filtro_data = request.args.get('filtro_data') or hoje.strftime('%Y-%m-%d')

    if request.method == 'POST':
        categoria = request.form['categoria']
        valor = float(request.form['valor'])
        data = request.form['data']
        data_formatada = datetime.strptime(data, '%Y-%m-%d').date()

        nova_venda = Movimentacao(
            tipo='receita',
            categoria=categoria,
            valor=valor,
            data=data_formatada,
            usuario_id=usuario_id
        )
        db.session.add(nova_venda)
        db.session.commit()
        flash('Venda registrada com sucesso!', 'success')
        return redirect(url_for('main.caixa'))

    vendas = Movimentacao.query.filter_by(tipo='receita', usuario_id=usuario_id)
    if filtro_data:
        try:
            data_filtrada = datetime.strptime(filtro_data, '%Y-%m-%d').date()
            vendas = vendas.filter(Movimentacao.data == data_filtrada)
        except ValueError:
            flash('Data inválida para filtro.', 'danger')
    vendas = vendas.order_by(Movimentacao.data.desc()).all()

    return render_template('caixa.html', movimentacoes=vendas, filtro_data=filtro_data, hoje=hoje.strftime('%Y-%m-%d'))
