import sqlite3

def criar_banco():
    conn = sqlite3.connect('movacash.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')
    # Cria usuário padrão se não existir
    cursor.execute("SELECT * FROM usuarios WHERE email = 'admin@top20.com'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                       ('Administrador', 'admin@top20.com', '1234'))
    conn.commit()
    conn.close()

def verificar_usuario(email, senha):
    conn = sqlite3.connect('movacash.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome, email FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        return {'nome': usuario[0], 'email': usuario[1]}
    return None
