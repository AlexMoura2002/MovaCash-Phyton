from . import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='vendedor')
    ultimo_acesso = db.Column(db.DateTime)

    # Relacionamentos
    movimentacoes = db.relationship('Movimentacao', backref='usuario', lazy=True)
    contas = db.relationship('Conta', backref='usuario', lazy=True)


class Movimentacao(db.Model):
    __tablename__ = 'movimentacoes'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # receita ou despesa
    categoria = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)


class Conta(db.Model):
    __tablename__ = 'contas'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # ✅ Campo adicionado
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
