import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'sua_chave_secreta_segura'
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'movacash.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
