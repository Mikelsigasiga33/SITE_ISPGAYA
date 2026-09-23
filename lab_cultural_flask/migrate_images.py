import pymysql
from config import Config

def migrate():
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT
        )
        
        tables = ['eventos', 'noticias', 'livros', 'espetaculos']
        
        with connection.cursor() as cursor:
            for table in tables:
                print(f"A verificar tabela '{table}'...")
                # Verificar se a coluna imagem já existe
                cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'imagem'")
                if cursor.fetchone():
                    print(f"A coluna 'imagem' já existe em '{table}'.")
                else:
                    print(f"A adicionar coluna 'imagem' a '{table}'...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN imagem VARCHAR(255) DEFAULT NULL")
        
        connection.commit()
        connection.close()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")

if __name__ == "__main__":
    migrate()
