import re
from app import get_db
from app.utils.security import sanitize


def _gerar_slug(nome: str) -> str:
    """Gera um slug a partir do nome (ex: 'Clube Tuna' -> 'clube-tuna')."""
    slug = nome.lower().strip()
    slug = re.sub(r'[àáâãä]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


class Clube:

    @staticmethod
    def get_all():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM clubes WHERE ativo = 1 ORDER BY nome")
            return cursor.fetchall()

    @staticmethod
    def get_all_admin():
        """Retorna todos os clubes, incluindo inativos (para backoffice)."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM clubes ORDER BY nome")
            return cursor.fetchall()

    @staticmethod
    def get_by_id(clube_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM clubes WHERE id = ?", (clube_id,))
            return cursor.fetchone()

    @staticmethod
    def get_by_slug(slug: str):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM clubes WHERE slug = ? AND ativo = 1", (slug,))
            return cursor.fetchone()

    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        nome = sanitize(dados.get('nome', ''))
        slug = _gerar_slug(nome)
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO clubes (nome, slug, descricao, icone, cor, local_reuniao, horario, imagem)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        nome,
                        slug,
                        sanitize(dados.get('descricao', '')),
                        sanitize(dados.get('icone', '🎵')),
                        sanitize(dados.get('cor', '#2563eb')),
                        sanitize(dados.get('local_reuniao', '')),
                        sanitize(dados.get('horario', '')),
                        sanitize(dados.get('imagem', ''))
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar clube: {e}")
            return False

    @staticmethod
    def editar(clube_id: int, dados: dict) -> bool:
        db = get_db()
        nome = sanitize(dados.get('nome', ''))
        slug = _gerar_slug(nome)
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """UPDATE clubes SET nome=?, slug=?, descricao=?, icone=?, cor=?,
                       local_reuniao=?, horario=?, imagem=?
                       WHERE id=?""",
                    (
                        nome,
                        slug,
                        sanitize(dados.get('descricao', '')),
                        sanitize(dados.get('icone', '🎵')),
                        sanitize(dados.get('cor', '#2563eb')),
                        sanitize(dados.get('local_reuniao', '')),
                        sanitize(dados.get('horario', '')),
                        sanitize(dados.get('imagem', '')),
                        clube_id
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar clube: {e}")
            return False

    @staticmethod
    def eliminar(clube_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM clubes WHERE id = ?", (clube_id,))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao eliminar clube: {e}")
            return False

    @staticmethod
    def alternar_estado(clube_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("UPDATE clubes SET ativo = 1 - ativo WHERE id = ?", (clube_id,))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao alternar estado do clube: {e}")
            return False
