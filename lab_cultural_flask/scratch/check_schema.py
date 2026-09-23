from app import create_app, get_db

app = create_app()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        for table in ['espetaculos', 'eventos']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"--- {table} ---")
            for col in columns:
                print(f"{col['name']} ({col['type']})")
