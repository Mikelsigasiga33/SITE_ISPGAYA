from app import create_app, get_db

app = create_app()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute('SELECT id, titulo, imagem FROM livros')
        livros = cursor.fetchall()
        for l in livros:
            print(f"ID: {l['id']} | Titulo: {l['titulo']} | Imagem: {l['imagem']}")
