from flask import Flask

app = Flask(__name__)
app.secret_key = 'movacash_supersegredo'

from app import routes  # 👈 Isso é OBRIGATÓRIO!
