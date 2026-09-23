import sqlite3
import os

db_path = 'lab_cultural.db'

# 1. Update main images
main_updates = [
    (1, 'img/eventos/evento_1.jpg'),
    (2, 'img/eventos/evento_2.jpg'),
    (3, 'img/eventos/evento_3.jpg'),
    (4, 'img/eventos/evento_4.jpg'),
    (5, 'img/eventos/evento_5.jpg'),
    (6, 'img/eventos/evento_6.jpg'),
    (7, 'img/eventos/evento_7.jpg'),
    (8, 'img/eventos/evento_8.jpg')
]

# 2. Add to gallery
gallery_data = [
    (1, 'Workshop de Fotografia - Perspetiva 1', 'img/eventos/evento_1_1.jpg'),
    (1, 'Workshop de Fotografia - Perspetiva 2', 'img/eventos/evento_1_2.jpg'),
    (1, 'Workshop de Fotografia - Perspetiva 3', 'img/eventos/evento_1_3.jpg'),
    (2, 'Noite de Jazz - Momento Musical', 'img/eventos/evento_2_1.jpg'),
    (3, 'Conferência IA - Orador Convidado', 'img/eventos/evento_3_1.jpg'),
    (5, 'Hackathon - Trabalho em Equipa', 'img/eventos/evento_5_1.jpg'),
    (6, 'Dia Aberto - Visita aos Laboratórios', 'img/eventos/evento_6_1.jpg'),
    (6, 'Dia Aberto - Sessão de Esclarecimento', 'img/eventos/evento_6_2.jpg')
]

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update main images
    for ev_id, img in main_updates:
        cursor.execute("UPDATE eventos SET imagem = ? WHERE id = ?", (img, ev_id))
    
    # Clear existing gallery for these events to avoid duplicates if re-run
    cursor.execute("DELETE FROM galeria_eventos")
    
    # Insert gallery images
    cursor.executemany(
        "INSERT INTO galeria_eventos (evento_id, titulo, imagem) VALUES (?, ?, ?)",
        gallery_data
    )
    
    conn.commit()
    print("Base de dados atualizada com sucesso!")
    conn.close()
else:
    print("Base de dados não encontrada.")
