from flask import Flask
from app import routes

def create_app():
    app = Flask(__name__)
    app.secret_key = 'chave-secreta'  # Pode usar qualquer texto

    app.register_blueprint(routes.routes)

    return app
