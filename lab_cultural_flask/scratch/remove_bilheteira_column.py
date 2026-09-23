import pymysql

def update_db():
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='lab_cultural',
            port=3307
        )
        with conn.cursor() as cursor:
            # Remover a coluna link_bilheteira
            print("Removendo coluna link_bilheteira da tabela espetaculos...")
            cursor.execute("ALTER TABLE espetaculos DROP COLUMN link_bilheteira;")
            
            conn.commit()
            print("Sucesso! Coluna removida.")
            
    except Exception as e:
        print(f"Erro ao atualizar BD: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_db()
