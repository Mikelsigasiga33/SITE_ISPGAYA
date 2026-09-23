import sqlite3

def run():
    db_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\lab_cultural.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ['mensagens_contacto', 'membros_teatro', 'membros_leitura', 'requisicoes_livros']
    for table in tables:
        print(f"\n--- {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        for col in cursor.fetchall():
            print(col)
    
    conn.close()

if __name__ == '__main__':
    run()
