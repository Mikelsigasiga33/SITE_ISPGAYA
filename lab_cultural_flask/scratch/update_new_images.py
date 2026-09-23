import sqlite3
import os

db_path = 'lab_cultural.db'

# 1. Update main images for 9 and 10
main_updates = [
    (9, 'img/eventos/evento_9.jpg'),
    (10, 'img/eventos/evento_10.jpg')
]

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update main images
    for ev_id, img in main_updates:
        cursor.execute("UPDATE eventos SET imagem = ? WHERE id = ?", (img, ev_id))
    
    conn.commit()
    print("Imagens dos eventos 9 e 10 atualizadas!")
    conn.close()
else:
    print("Base de dados não encontrada.")
