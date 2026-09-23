import sqlite3

def run():
    db_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\lab_cultural.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- INICIANDO LIMPEZA DE REGISTOS INATIVOS ---")
    
    # Limpar espetaculos inativos
    cursor.execute("DELETE FROM espetaculos WHERE ativo = 0")
    print(f"Removidos {cursor.rowcount} registos inativos da tabela 'espetaculos'.")
    
    # Limpar eventos inativos (se houver)
    cursor.execute("DELETE FROM eventos WHERE ativo = 0")
    print(f"Removidos {cursor.rowcount} registos inativos da tabela 'eventos'.")
    
    conn.commit()
    conn.close()
    print("\n--- LIMPEZA CONCLUÍDA ---")

if __name__ == '__main__':
    run()
