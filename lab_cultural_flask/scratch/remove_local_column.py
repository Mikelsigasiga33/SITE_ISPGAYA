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
            fks_to_drop = [
                'fk_esp_loc',
                'fk_esp_local',
                'fk_esp_local_res',
                'fk_espetaculo_local_final',
                'fk_res_espetaculo_local'
            ]
            
            for fk in fks_to_drop:
                print(f"Tentando remover a foreign key '{fk}'...")
                try:
                    cursor.execute(f"ALTER TABLE espetaculos DROP FOREIGN KEY {fk};")
                    print(f"FK '{fk}' removida.")
                except Exception as e:
                    print(f"Erro ao remover FK '{fk}': {e}")

            # Agora remover o index que pode estar a bloquear
            print("Tentando remover o index 'fk_espetaculo_local_v3'...")
            try:
                cursor.execute("ALTER TABLE espetaculos DROP INDEX fk_espetaculo_local_v3;")
                print("Index removido.")
            except Exception as e:
                print(f"Erro ao remover index: {e}")

            # Finalmente remover a coluna
            print("Removendo coluna local_id...")
            cursor.execute("ALTER TABLE espetaculos DROP COLUMN local_id;")
            
            conn.commit()
            print("Sucesso! Coluna removida.")
            
    except Exception as e:
        print(f"Erro fatal: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_db()
