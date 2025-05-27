import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def criar_banco():
    conexao = sqlite3.connect('movacash.db')
    cursor = conexao.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')

    # Tabela de movimentações financeiras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_email TEXT NOT NULL,
            tipo TEXT NOT NULL,  -- 'receita' ou 'despesa'
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL
        )
    ''')

    conexao.commit()
    conexao.close()

# Funções de usuário
def verificar_login(email, senha):
    conexao = sqlite3.connect('movacash.db')
    cursor = conexao.cursor()

    cursor.execute("SELECT senha FROM usuarios WHERE email = ?", (email,))
    resultado = cursor.fetchone()
    conexao.close()

    if resultado:
        senha_armazenada = resultado[0]
        return check_password_hash(senha_armazenada, senha)
    return False

def verificar_usuario_existente(email):
    conexao = sqlite3.connect('movacash.db')
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    usuario = cursor.fetchone()
    conexao.close()

    return usuario is not None

def criar_usuario(nome, email, senha):
    senha_criptografada = generate_password_hash(senha)
    conexao = sqlite3.connect('movacash.db')
    cursor = conexao.cursor()

    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                   (nome, email, senha_criptografada))

    conexao.commit()
    conexao.close()

# Função para registrar movimentação
def adicionar_movimentacao(usuario_email, tipo, categoria, valor, data):
    conexao = sqlite3.connect('movacash.db')
    cursor = conexao.cursor()

    cursor.execute('''
        INSERT INTO movimentacoes (usuario_email, tipo, categoria, valor, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (usuario_email, tipo, categoria, valor, data))

    conexao.commit()
    conexao.close()

# Buscar movimentações
def obter_movimentacoes(usuario_email):
    conexao = sqlite3.connect('movacash.db')
    cursor = conexao.cursor()

    cursor.execute('''
        SELECT tipo, categoria, valor, data
        FROM movimentacoes
        WHERE usuario_email = ?
        ORDER BY data DESC
    ''', (usuario_email,))

    movimentacoes = cursor.fetchall()
    conexao.close()
    return movimentacoes
