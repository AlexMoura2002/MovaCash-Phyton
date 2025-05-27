from app import create_app
from app.models import criar_banco

criar_banco()  # Cria o banco se ainda não existir

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
