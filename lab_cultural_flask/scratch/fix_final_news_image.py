import sqlite3

def run():
    db_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\lab_cultural.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ID verificado pelo subagente: photo-1549923746-c502d488b3ea
    img_id = "photo-1549923746-c502d488b3ea"
    
    cursor.execute("UPDATE noticias SET imagem = ? WHERE id = 7", (img_id,))
    
    conn.commit()
    conn.close()
    print(f"Notícia ID 7: Imagem atualizada para {img_id}")

if __name__ == '__main__':
    run()
