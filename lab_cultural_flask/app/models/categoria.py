from app import get_db
from app.utils.security import sanitize


class Categoria:

    @staticmethod
    def get_all():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT id, nome, icone, cor FROM categorias ORDER BY nome")
            return cursor.fetchall()

    @staticmethod
    def get_by_id(cat_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT id, nome, icone, cor FROM categorias WHERE id = ?", (cat_id,))
            return cursor.fetchone()

    @staticmethod
    def get_by_name(nome: str):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT id, nome, icone, cor FROM categorias WHERE nome = ?", (nome,))
            return cursor.fetchone()

    @staticmethod
    def criar(nome: str, icone: str = '🎭', cor: str = '#2563eb') -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO categorias (nome, icone, cor) VALUES (?, ?, ?)",
                    (sanitize(nome), sanitize(icone), sanitize(cor))
                )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def editar(cat_id: int, nome: str, icone: str, cor: str) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE categorias SET nome = ?, icone = ?, cor = ? WHERE id = ?",
                    (sanitize(nome), sanitize(icone), sanitize(cor), cat_id)
                )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def eliminar(cat_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
