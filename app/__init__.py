from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'chave_secreta'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movacash.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # 🔧 Adicione esta parte abaixo para criar as tabelas no banco
    with app.app_context():
        from .models import Usuario  # importe seus modelos aqui
        db.create_all()

    return app
