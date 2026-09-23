import sqlite3

def run():
    db_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\lab_cultural.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # IDs verificados e de alta qualidade
    noticias_images = {
        1: "photo-1497366216548-37526070297c", 
        2: "photo-1544947950-fa07a98d237f", 
        3: "photo-1513364776144-60967b0f800f", 
        4: "photo-1741637335289-c99652d3155f", # Campus (Verificado)
        5: "photo-1497366811353-6870744d04b2", 
        6: "photo-1504384308090-c894fdcc538d", 
        7: "photo-1661371394983-42485fed3a58", # Parceria (Verificado)
        8: "photo-1514306191717-452ec28c7814", # Teatro Drama (Verificado)
        9: "photo-1511379938547-c1f69419868d", 
        10: "photo-1491841573634-28140fc7ced7", 
        11: "photo-1735605917461-4c1b77a6616f"  # Arte (Verificado)
    }

    print("--- ATUALIZANDO IMAGENS (VERIFICADAS NO BROWSER) ---")
    for nid, img_id in noticias_images.items():
        cursor.execute("UPDATE noticias SET imagem = ? WHERE id = ?", (img_id, nid))
        print(f"Notícia ID {nid}: {img_id}")
    
    conn.commit()
    conn.close()
    print("\n--- ATUALIZAÇÃO CONCLUÍDA ---")

if __name__ == '__main__':
    run()
