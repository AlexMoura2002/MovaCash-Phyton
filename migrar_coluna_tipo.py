import sqlite3

# Caminho do banco de dados
caminho_db = 'instance/movacash.db'

# Conectando ao banco
conn = sqlite3.connect(caminho_db)
cursor = conn.cursor()

try:
    # Tenta adicionar a nova coluna
    cursor.execute("ALTER TABLE contas ADD COLUMN tipo TEXT NOT NULL DEFAULT 'pagar'")
    print("✅ Coluna 'tipo' adicionada com sucesso.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ A coluna 'tipo' já existe.")
    else:
        print("❌ Erro ao adicionar coluna:", e)

conn.commit()
conn.close()
