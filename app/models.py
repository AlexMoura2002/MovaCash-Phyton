from flask_sqlalchemy import SQLAlchemy
from datetime import date
from . import db  # Isso funciona agora porque não ocorre circular import

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

class Movimentacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # receita ou despesa
    categoria = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, default=date.today)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pago ou pendente
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
