from app import create_app, get_db

app = create_app()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        # Primeiro, vamos ver o que temos
        cursor.execute("SELECT id, titulo, imagem FROM livros")
        livros = cursor.fetchall()
        
        for l in livros:
            img = l['imagem']
            if img and not img.startswith('img/') and not img.startswith('uploads/'):
                new_img = f"img/leitura/{img}"
                print(f"Updating ID {l['id']}: {img} -> {new_img}")
                cursor.execute("UPDATE livros SET imagem = ? WHERE id = ?", (new_img, l['id']))
        
    db.commit()
    print("Concluído.")
