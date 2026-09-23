from app import create_app, get_db

app = create_app()
with app.app_context():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("ALTER TABLE espetaculos DROP COLUMN classificacao_etaria")
        db.commit()
        print("Coluna 'classificacao_etaria' removida da tabela 'espetaculos'.")
    except Exception as e:
        print(f"Erro ao remover coluna: {e}")
