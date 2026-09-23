from app import get_db, create_app

app = create_app()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id, titulo, data_publicacao, NOW() as agora FROM eventos")
        print("--- EVENTOS ---")
        for row in cursor.fetchall():
            print(f"ID: {row['id']} | Titulo: {row['titulo']} | Pub: {row['data_publicacao']} | Agora: {row['agora']}")
        
        cursor.execute("SELECT id, titulo, data_publicacao, NOW() as agora FROM espetaculos")
        print("\n--- ESPETACULOS ---")
        for row in cursor.fetchall():
            print(f"ID: {row['id']} | Titulo: {row['titulo']} | Pub: {row['data_publicacao']} | Agora: {row['agora']}")
