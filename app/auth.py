from flask import request, jsonify
from .models import User
from . import db, bcrypt

def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Login realizado com sucesso", "user": user.email}), 200
    return jsonify({"message": "Email ou senha inválidos"}), 401
