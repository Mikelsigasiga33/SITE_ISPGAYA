from app import get_db
from app.utils.security import sanitize


class Noticia:

    @staticmethod
    def get_all(filtros: dict = None, pagina: int = 1, por_pagina: int = 9):
        db = get_db()
        offset = (pagina - 1) * por_pagina
        
        where_clause = "WHERE n.ativo = 1"
        params = []
        
        if filtros:
            if filtros.get('categoria_id'):
                where_clause += " AND n.categoria_id = ?"
                params.append(filtros['categoria_id'])
            if filtros.get('q'):
                where_clause += " AND n.titulo LIKE ?"
                params.append(f"%{filtros['q']}%")
            
        with db.cursor() as cursor:
            # Pegar o total com filtros
            count_query = f"SELECT COUNT(*) as total FROM noticias n {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Pegar os resultados com filtros
            cursor.execute(
                f"""SELECT n.*, c.nome AS categoria_nome, c.icone AS categoria_icone
                   FROM noticias n
                   LEFT JOIN categorias c ON n.categoria_id = c.id
                   {where_clause}
                   ORDER BY n.publicado_em DESC
                   LIMIT ? OFFSET ?""",
                params + [por_pagina, offset]
            )
            return cursor.fetchall(), total

    @staticmethod
    def get_by_id(noticia_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT n.*, c.nome AS categoria_nome, c.icone AS categoria_icone
                   FROM noticias n
                   LEFT JOIN categorias c ON n.categoria_id = c.id
                   WHERE n.id = ? AND n.ativo = 1""",
                (noticia_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_destaques(limite: int = 3):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT n.*, c.nome AS categoria_nome, c.icone AS categoria_icone
                   FROM noticias n
                   LEFT JOIN categorias c ON n.categoria_id = c.id
                   WHERE n.ativo = 1 AND n.destaque = 1
                   ORDER BY n.publicado_em DESC LIMIT ?""",
                (limite,)
            )
            return cursor.fetchall()

    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO noticias (titulo, resumo, conteudo, categoria_id, publicado_em, destaque, imagem)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('resumo', '')),
                        sanitize(dados.get('conteudo', '')),
                        dados.get('categoria_id') or None,
                        dados.get('publicado_em') or None,
                        1 if dados.get('destaque') else 0,
                        dados.get('imagem')
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar notícia: {e}")
            return False

    @staticmethod
    def editar(noticia_id: int, dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """UPDATE noticias SET titulo=?, resumo=?, conteudo=?,
                       categoria_id=?, publicado_em=?, destaque=?, imagem=?
                       WHERE id=?""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('resumo', '')),
                        sanitize(dados.get('conteudo', '')),
                        dados.get('categoria_id') or None,
                        dados.get('publicado_em') or None,
                        1 if dados.get('destaque') else 0,
                        dados.get('imagem'),
                        noticia_id
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar notícia: {e}")
            return False

    @staticmethod
    def eliminar(noticia_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("UPDATE noticias SET ativo = 0 WHERE id = ?", (noticia_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
