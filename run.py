from app import app
from app.models import criar_banco

criar_banco()

if __name__ == '__main__':
    app.run(debug=True)
