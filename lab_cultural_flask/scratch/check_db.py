import sqlite3
import os
from datetime import date

db_path = 'lab_cultural.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Hoje: {date.today()}")
    
    cursor.execute("SELECT id, titulo, data_evento FROM espetaculos WHERE ativo = 1")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row['id']} | Título: {row['titulo']} | Data: {row['data_evento']}")
        
    cursor.execute("SELECT espetaculo_id, count(*) as total FROM galeria_teatro GROUP BY espetaculo_id")
    gal = cursor.fetchall()
    print("\nGaleria (fotos por espetáculo):")
    for g in gal:
        print(f"Espetáculo ID: {g['espetaculo_id']} | Fotos: {g['total']}")
        
    conn.close()
else:
    print(f"Base de dados não encontrada em {os.path.abspath(db_path)}")
