from app import create_app, db
from app.models import Usuario
from datetime import datetime

app = create_app()

with app.app_context():
    # Verifica se já existe um admin
    existente = Usuario.query.filter_by(email='admin@admin.com').first()
    if existente:
        print("⚠️ Usuário admin já existe.")
    else:
        admin = Usuario(
            nome='Admin',
            email='admin@admin.com',
            senha='123',  # você pode alterar a senha aqui
            tipo='admin',
            ultimo_acesso=datetime.now()
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado com sucesso!")
