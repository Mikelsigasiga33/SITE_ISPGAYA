from app import get_db, create_app

app = create_app()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        try:
            cursor.execute("""
                ALTER TABLE eventos 
                ADD COLUMN tipo_ingresso ENUM('gratis', 'pago') DEFAULT 'gratis',
                ADD COLUMN preco DECIMAL(10,2) DEFAULT 0.00,
                ADD COLUMN limite_bilhetes INT NULL
            """)
            db.commit()
            print("Colunas (tipo_ingresso, preco, limite_bilhetes) adicionadas com sucesso!")
        except Exception as e:
            print(f"Erro na migração: {e}")
