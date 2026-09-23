from app import get_db
import uuid

class InscricaoTeatro:
    @staticmethod
    def criar(dados):
        """Regista uma nova inscrição no clube de teatro."""
        db = get_db()
        try:
            codigo = str(uuid.uuid4().hex[:8]).upper()
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO inscricoes_teatro (espetaculo_id, nome_aluno, email_aluno, codigo_inscricao, lugares)
                       VALUES (?, ?, ?, ?, ?)""",
                    (dados['espetaculo_id'], dados['nome'], dados['email'], codigo, dados.get('lugares'))
                )
            db.commit()
            return codigo
        except Exception as e:
            print(f"Erro ao criar inscrição: {e}")
            return None

    @staticmethod
    def verificar_duplicado(espetaculo_id, email):
        """Verifica se o aluno já está inscrito neste espetáculo."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM inscricoes_teatro WHERE espetaculo_id = ? AND email_aluno = ?",
                (espetaculo_id, email)
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_lugares_ocupados(espetaculo_id):
        """Retorna uma lista de lugares já ocupados para um espetáculo."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT lugares FROM inscricoes_teatro WHERE espetaculo_id = ? AND lugares IS NOT NULL",
                (espetaculo_id,)
            )
            rows = cursor.fetchall()
            ocupados = []
            for row in rows:
                if row['lugares']:
                    ocupados.extend(row['lugares'].split(','))
            return [lugar.strip() for lugar in ocupados if lugar.strip()]
            
    @staticmethod
    def get_inscricoes_by_espetaculo(espetaculo_id):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM inscricoes_teatro WHERE espetaculo_id = ? ORDER BY data_inscricao DESC",
                (espetaculo_id,)
            )
            return cursor.fetchall()
