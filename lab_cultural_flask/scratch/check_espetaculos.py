import sqlite3
import os

db_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\lab_cultural.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- Espetáculos ---")
    cursor.execute("SELECT id, titulo, descricao FROM espetaculos WHERE ativo = 1")
    for row in cursor.fetchall():
        print(f"ID: {row['id']} | Título: {row['titulo']}")
        # print(f"Desc: {row['descricao'][:50]}...")
    
    conn.close()
else:
    print("DB not found")
