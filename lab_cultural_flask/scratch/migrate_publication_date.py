from app import get_db, create_app

app = create_app()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        print("--- EVENTOS ---")
        cursor.execute("DESCRIBE eventos")
        for col in cursor.fetchall():
            print(col)
        
        print("\n--- ESPETACULOS ---")
        cursor.execute("DESCRIBE espetaculos")
        for col in cursor.fetchall():
            print(col)

        # ALTER TABLE to add data_publicacao if it doesn't exist
        try:
            cursor.execute("ALTER TABLE eventos ADD COLUMN data_publicacao DATETIME DEFAULT NULL")
            print("Added data_publicacao to eventos")
        except Exception as e:
            print(f"Error adding to eventos: {e}")

        try:
            cursor.execute("ALTER TABLE espetaculos ADD COLUMN data_publicacao DATETIME DEFAULT NULL")
            print("Added data_publicacao to espetaculos")
        except Exception as e:
            print(f"Error adding to espetaculos: {e}")
            
    db.commit()
