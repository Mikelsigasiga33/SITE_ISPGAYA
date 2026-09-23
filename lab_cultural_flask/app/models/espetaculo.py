from app import get_db
from app.utils.security import sanitize


class Espetaculo:

    @staticmethod
    def get_agenda(filtros: dict = None, apenas_futuros: bool = False):
        db = get_db()
        filtros = filtros or {}
        conditions = ["e.ativo = 1"]
        if apenas_futuros:
            conditions.append("(e.data_publicacao IS NULL OR e.data_publicacao <= datetime('now', 'localtime'))")
        params = []
        
        if apenas_futuros:
            conditions.append("e.data_evento >= date('now', 'localtime')")
            
        if filtros.get('q'):
            conditions.append("e.titulo LIKE ?")
            params.append(f"%{filtros['q']}%")
            
        if filtros.get('tipo'):
            conditions.append("e.tipo = ?")
            params.append(filtros['tipo'])
            
        if filtros.get('data_de'):
            conditions.append("e.data_evento >= ?")
            params.append(filtros['data_de'])
            
        if filtros.get('data_ate'):
            conditions.append("e.data_evento <= ?")
            params.append(filtros['data_ate'])
            
        where = " AND ".join(conditions)
        
        # Ordenação
        sort_field = filtros.get('ordem', 'data_evento')
        sort_dir = filtros.get('dir', 'ASC')
        
        # Lista branca de campos para evitar SQL Injection
        valid_fields = {
            'data_evento': 'e.data_evento',
            'titulo': 'e.titulo',
            'tipo': 'e.tipo',
            'destaque': 'e.destaque',
            'criado_em': 'e.criado_em',
            'id': 'e.id'
        }
        field = valid_fields.get(sort_field, 'e.data_evento')
        direction = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'

        with db.cursor() as cursor:
            cursor.execute(
                f"""SELECT e.*, 'ISPGAYA' AS local, c.nome AS categoria_nome
                   FROM espetaculos e
                   LEFT JOIN categorias c ON e.categoria_id = c.id
                   WHERE {where}
                   ORDER BY {field} {direction}""",
                params
            )
            return cursor.fetchall()

    @staticmethod
    def get_all_paginated(filtros: dict = None, pagina: int = 1, por_pagina: int = 9):
        db = get_db()
        filtros = filtros or {}
        conditions = ["ativo = 1"]
        params = []
        
        # Filtro de publicação para o frontoffice
        if filtros.get('apenas_publicados'):
            conditions.append("(data_publicacao IS NULL OR data_publicacao <= datetime('now', 'localtime'))")

        # Filtro de eventos futuros apenas
        if filtros.get('apenas_futuros'):
            conditions.append("data_evento >= date('now', 'localtime')")

        if filtros.get('tipo'):
            conditions.append("tipo = ?")
            params.append(filtros['tipo'])
            
        if filtros.get('entrada'):
            conditions.append("entrada = ?")
            params.append(filtros['entrada'])



        if filtros.get('q'):
            conditions.append("titulo LIKE ?")
            params.append(f"%{filtros['q']}%")

        if filtros.get('data_de'):
            conditions.append("data_evento >= ?")
            params.append(filtros['data_de'])

        if filtros.get('destaque'):
            conditions.append("destaque = 1")

        where = " AND ".join(conditions)
        offset = (pagina - 1) * por_pagina

        with db.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as total FROM espetaculos WHERE {where}", params)
            total = cursor.fetchone()['total']

            cursor.execute(
                f"""SELECT e.*, 'ISPGAYA' AS local, c.nome AS categoria_nome
                    FROM espetaculos e
                    LEFT JOIN categorias c ON e.categoria_id = c.id
                    WHERE {where}
                    ORDER BY e.data_evento ASC
                    LIMIT ? OFFSET ?""",
                params + [por_pagina, offset]
            )
            return cursor.fetchall(), total

    @staticmethod
    def contar_inscritos(esp_id: int) -> int:
        db = get_db()
        with db.cursor() as cursor:
            # No teatro as inscrições são diretas, não há coluna 'estado'
            cursor.execute(
                "SELECT COUNT(*) as total FROM inscricoes_teatro WHERE espetaculo_id = ?",
                (esp_id,)
            )
            row = cursor.fetchone()
            return row['total'] if row else 0

    @staticmethod
    def get_by_id(esp_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT e.*, 'ISPGAYA' AS local, c.nome AS categoria_nome
                   FROM espetaculos e
                   LEFT JOIN categorias c ON e.categoria_id = c.id
                   WHERE e.id = ? AND e.ativo = 1""", (esp_id,)
            )
            espetaculo = cursor.fetchone()
            
            if espetaculo:
                # Buscar elenco e encenação na tabela de equipa
                cursor.execute(
                    """SELECT ent.nome, ee.funcao
                       FROM espetaculo_equipa ee
                       JOIN entidades_culturais ent ON ee.entidade_id = ent.id
                       WHERE ee.espetaculo_id = ?""", (esp_id,)
                )
                equipa = cursor.fetchall()
                
                elenco = [m['nome'] for m in equipa if m['funcao'] == 'Ator']
                encenadores = [m['nome'] for m in equipa if m['funcao'] == 'Encenador']
                
                espetaculo['elenco'] = ", ".join(elenco)
                espetaculo['encenacao'] = ", ".join(encenadores)
                
            return espetaculo

    @staticmethod
    def get_destaques(limite: int = 3):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT e.*, 'ISPGAYA' AS local, c.nome AS categoria_nome
                   FROM espetaculos e
                   LEFT JOIN categorias c ON e.categoria_id = c.id
                   WHERE e.ativo = 1 AND e.destaque = 1
                   AND (e.data_publicacao IS NULL OR e.data_publicacao <= datetime('now', 'localtime'))
                   ORDER BY e.data_evento DESC LIMIT ?""",
                (limite,)
            )
            return cursor.fetchall()

    @staticmethod
    def toggle_destaque(esp_id: int) -> bool:
        """Alterna o estado de destaque de um espetáculo (0 -> 1 ou 1 -> 0)."""
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE espetaculos SET destaque = CASE WHEN destaque = 1 THEN 0 ELSE 1 END WHERE id = ?",
                    (esp_id,)
                )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO espetaculos (titulo, descricao, tipo, data_evento, hora, entrada, preco, imagem, duracao, limite_filas, data_publicacao, destaque)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('descricao', '')),
                        dados.get('tipo', 'espetaculo'),
                        dados.get('data_evento') or None,
                        dados.get('hora') or None,
                        dados.get('entrada', 'gratuita'),
                        dados.get('preco') or None,
                        dados.get('imagem'),
                        sanitize(dados.get('duracao', '')),
                        int(dados.get('limite_filas')) if dados.get('limite_filas') else 8,
                        dados.get('data_publicacao') if dados.get('usar_agendamento') else None,
                        1 if dados.get('destaque') else 0
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar espetáculo: {e}")
            return False

    @staticmethod
    def editar(esp_id: int, dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """UPDATE espetaculos SET titulo=?, descricao=?, tipo=?,
                       data_evento=?, hora=?, entrada=?, preco=?, imagem=?,
                       duracao=?, limite_filas=?, data_publicacao=?, destaque=?
                       WHERE id=?""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('descricao', '')),
                        dados.get('tipo', 'espetaculo'),
                        dados.get('data_evento') or None,
                        dados.get('hora') or None,
                        dados.get('entrada', 'gratuita'),
                        dados.get('preco') or None,
                        dados.get('imagem'),
                        sanitize(dados.get('duracao', '')),
                        int(dados.get('limite_filas')) if dados.get('limite_filas') else 8,
                        dados.get('data_publicacao') if dados.get('usar_agendamento') else None,
                        1 if dados.get('destaque') else 0,
                        esp_id
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar espetáculo: {e}")
            return False

    @staticmethod
    def eliminar(esp_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("UPDATE espetaculos SET ativo = 0 WHERE id = ?", (esp_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def get_galeria():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT g.* FROM galeria_teatro g
                   INNER JOIN espetaculos e ON g.espetaculo_id = e.id
                   WHERE g.ativo = 1 AND e.data_evento < date('now', 'localtime')
                   ORDER BY g.ordem ASC, g.criado_em DESC"""
            )
            return cursor.fetchall()

    @staticmethod
    def get_fotos_by_espetaculo(esp_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM galeria_teatro WHERE espetaculo_id = ? AND ativo = 1 ORDER BY ordem ASC, criado_em DESC",
                (esp_id,)
            )
            return cursor.fetchall()

    @staticmethod
    def adicionar_foto_galeria(esp_id: int, titulo: str, imagem: str) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO galeria_teatro (espetaculo_id, titulo, imagem, ativo)
                       VALUES (?, ?, ?, 1)""",
                    (esp_id, sanitize(titulo), imagem)
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao adicionar foto à galeria: {e}")
            return False

    @staticmethod
    def eliminar_foto_galeria(foto_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("UPDATE galeria_teatro SET ativo = 0 WHERE id = ?", (foto_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False



class MembroTeatro:
    
    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO membros_teatro (nome, email)
                       VALUES (?, ?)""",
                    (
                        sanitize(dados.get('nome', '')),
                        sanitize(dados.get('email', ''))
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao registar membro no teatro: {e}")
            return False

    @staticmethod
    def verificar_duplicado(email: str) -> bool:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM membros_teatro WHERE email = ?",
                (sanitize(email),)
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_all():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM membros_teatro ORDER BY criado_em DESC")
            return cursor.fetchall()

    @staticmethod
    def get_by_id(membro_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM membros_teatro WHERE id = ?", (membro_id,))
            return cursor.fetchone()

    @staticmethod
    def atualizar_estado(membro_id: int, estado: str) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE membros_teatro SET estado = ? WHERE id = ?",
                    (estado, membro_id)
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao atualizar estado do membro: {e}")
            return False
