from app import get_db
from app.utils.security import sanitize


class Livro:

    @staticmethod
    def get_all(filtros: dict = None):
        db = get_db()
        filtros = filtros or {}
        conditions = []
        params = []
        
        if filtros.get('q'):
            conditions.append("titulo LIKE ?")
            params.append(f"%{filtros['q']}%")
            
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        
        # Ordenação
        sort_field = filtros.get('ordem', 'titulo')
        sort_dir = filtros.get('dir', 'ASC')
        
        valid_fields = {
            'titulo': 'titulo',
            'autor': 'autor',
            'ano': 'ano',
            'destaque': 'destaque',
            'criado_em': 'id'
        }
        field = valid_fields.get(sort_field, 'titulo')
        direction = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'

        with db.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM livros {where} ORDER BY {field} {direction}",
                params
            )
            return cursor.fetchall()

    @staticmethod
    def get_all_paginated(filtros=None, pagina=1, por_pagina=12):
        db = get_db()
        filtros = filtros or {}
        conditions = []
        params = []
        
        if filtros.get('q'):
            conditions.append("LOWER(titulo) LIKE LOWER(?)")
            params.append(f"%{filtros['q']}%")
        
        if filtros.get('genero'):
            conditions.append("genero = ?")
            params.append(filtros['genero'])
            
        if filtros.get('disponibilidade') == 'disponivel':
            conditions.append("esta_disponivel = 1")
        elif filtros.get('disponibilidade') == 'indisponivel':
            conditions.append("esta_disponivel = 0")
            
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (pagina - 1) * por_pagina
        
        with db.cursor() as cursor:
            # Contar total
            cursor.execute(f"SELECT COUNT(*) as total FROM livros {where}", params)
            total = cursor.fetchone()['total']
            
            # Buscar página com join para obter a data de entrega limite se estiver requisitado
            query = f"""
                SELECT l.*, r.data_entrega_limite, r.estado as req_estado
                FROM livros l
                LEFT JOIN requisicoes_livros r ON l.id = r.livro_id AND r.estado IN ('Levantado', 'Aceite', 'Pendente')
                {where.replace('esta_disponivel', 'l.esta_disponivel').replace('genero', 'l.genero').replace('titulo', 'l.titulo')}
                ORDER BY l.id DESC LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [por_pagina, offset])
            livros = [dict(row) for row in cursor.fetchall()]
            
            # Calcular dias restantes para cada livro
            from app.models.livro import RequisicaoLivro
            for l in livros:
                if l.get('data_entrega_limite') and l.get('req_estado') == 'Levantado':
                    l['dias_restantes'] = RequisicaoLivro.calcular_dias_restantes(l['data_entrega_limite'])
                else:
                    l['dias_restantes'] = None
            
        return livros, total

    @staticmethod
    def get_generos():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT DISTINCT genero FROM livros WHERE genero IS NOT NULL AND genero != '' ORDER BY genero ASC")
            return [row['genero'] for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(livro_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM livros WHERE id = ?", (livro_id,))
            return cursor.fetchone()

    @staticmethod
    def get_destaques(limite: int = 3):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM livros WHERE destaque = 1 ORDER BY id DESC LIMIT ?",
                (limite,)
            )
            return cursor.fetchall()

    @staticmethod
    def toggle_destaque(livro_id: int) -> bool:
        """Alterna o estado de destaque de um livro (0 -> 1 ou 1 -> 0)."""
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE livros SET destaque = CASE WHEN destaque = 1 THEN 0 ELSE 1 END WHERE id = ?",
                    (livro_id,)
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
                    """INSERT INTO livros (titulo, autor, sinopse, ano, genero, mes_selecao, destaque, imagem, url_biblioteca, esta_disponivel)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('autor', '')),
                        sanitize(dados.get('sinopse', '')),
                        dados.get('ano') or None,
                        sanitize(dados.get('genero', '')),
                        sanitize(dados.get('mes_selecao', '')),
                        1 if dados.get('destaque') else 0,
                        dados.get('imagem'),
                        sanitize(dados.get('url_biblioteca', '')),
                        1 if str(dados.get('esta_disponivel')) == '1' else 0
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar livro: {e}")
            return False

    @staticmethod
    def editar(livro_id: int, dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """UPDATE livros SET titulo=?, autor=?, sinopse=?, ano=?,
                       genero=?, mes_selecao=?, destaque=?, imagem=?, 
                       url_biblioteca=?, esta_disponivel=? WHERE id=?""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('autor', '')),
                        sanitize(dados.get('sinopse', '')),
                        dados.get('ano') or None,
                        sanitize(dados.get('genero', '')),
                        sanitize(dados.get('mes_selecao', '')),
                        1 if dados.get('destaque') else 0,
                        dados.get('imagem'),
                        sanitize(dados.get('url_biblioteca', '')),
                        1 if str(dados.get('esta_disponivel')) == '1' else 0,
                        livro_id
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar livro: {e}")
            return False

    @staticmethod
    def eliminar(livro_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False


class SessaoLeitura:

    @staticmethod
    def get_calendario(filtros: dict = None, apenas_futuros: bool = False):
        db = get_db()
        filtros = filtros or {}
        conditions = []
        params = []
        
        if apenas_futuros:
            conditions.append("s.data_sessao >= date('now', 'localtime')")
            
        if filtros.get('q'):
            conditions.append("s.tema LIKE ?")
            params.append(f"%{filtros['q']}%")
            
        if filtros.get('livro_id'):
            conditions.append("s.livro_id = ?")
            params.append(filtros['livro_id'])
            
        if filtros.get('data_de'):
            conditions.append("s.data_sessao >= ?")
            params.append(filtros['data_de'])
            
        if filtros.get('data_ate'):
            conditions.append("s.data_sessao <= ?")
            params.append(filtros['data_ate'])
            
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        
        # Ordenação
        sort_field = filtros.get('ordem', 'data_sessao')
        sort_dir = filtros.get('dir', 'ASC')
        
        valid_fields = {
            'data_sessao': 's.data_sessao',
            'tema': 's.tema',
            'criado_em': 's.criado_em',
            'id': 's.id'
        }
        field = valid_fields.get(sort_field, 's.data_sessao')
        direction = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'

        with db.cursor() as cursor:
            cursor.execute(
                f"""SELECT s.*, l.titulo AS livro_titulo, COALESCE(loc.nome, 'Biblioteca ISPGAYA') AS local
                   FROM sessoes_leitura s
                   LEFT JOIN livros l ON s.livro_id = l.id
                   LEFT JOIN locais loc ON s.local_id = loc.id
                   {where}
                   ORDER BY {field} {direction}""",
                params
            )
            return cursor.fetchall()

    @staticmethod
    def get_by_id(sessao_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT s.*, COALESCE(loc.nome, 'Biblioteca ISPGAYA') AS local
                   FROM sessoes_leitura s
                   LEFT JOIN locais loc ON s.local_id = loc.id
                   WHERE s.id = ?""", (sessao_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO sessoes_leitura (livro_id, data_sessao, hora, local_id, tema, descricao)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        dados.get('livro_id') or None,
                        dados.get('data_sessao') or None,
                        dados.get('hora') or None,
                        dados.get('local_id'),
                        sanitize(dados.get('tema', '')),
                        sanitize(dados.get('descricao', ''))
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar sessão: {e}")
            return False

    @staticmethod
    def editar(sessao_id: int, dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """UPDATE sessoes_leitura SET livro_id=?, data_sessao=?, hora=?,
                       local_id=?, tema=?, descricao=? WHERE id=?""",
                    (
                        dados.get('livro_id') or None,
                        dados.get('data_sessao') or None,
                        dados.get('hora') or None,
                        dados.get('local_id'),
                        sanitize(dados.get('tema', '')),
                        sanitize(dados.get('descricao', '')),
                        sessao_id
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar sessão: {e}")
            return False

    @staticmethod
    def eliminar(sessao_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM sessoes_leitura WHERE id = ?", (sessao_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

class InscricaoLeitura:
    
    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO inscricoes_leitura (sessao_id, nome, email)
                       VALUES (?, ?, ?)""",
                    (
                        dados.get('sessao_id'),
                        sanitize(dados.get('nome', '')),
                        sanitize(dados.get('email', ''))
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao inscrever na sessão de leitura: {e}")
            return False

    @staticmethod
    def verificar_duplicado(sessao_id: int, email: str) -> bool:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM inscricoes_leitura WHERE sessao_id = ? AND email = ?",
                (sessao_id, sanitize(email))
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_inscricoes_by_sessao(sessao_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT id, nome, email, criado_em 
                   FROM inscricoes_leitura 
                   WHERE sessao_id = ? 
                   ORDER BY criado_em DESC""",
                (sessao_id,)
            )
            return cursor.fetchall()

class MembroLeitura:
    
    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO membros_leitura (nome, email)
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
            print(f"Erro ao registar membro na leitura: {e}")
            return False

    @staticmethod
    def verificar_duplicado(email: str) -> bool:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM membros_leitura WHERE email = ?",
                (sanitize(email),)
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_all():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM membros_leitura ORDER BY criado_em DESC")
            return cursor.fetchall()

    @staticmethod
    def get_by_id(membro_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM membros_leitura WHERE id = ?", (membro_id,))
            return cursor.fetchone()

    @staticmethod
    def atualizar_estado(membro_id: int, estado: str) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE membros_leitura SET estado = ? WHERE id = ?",
                    (estado, membro_id)
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao atualizar estado do membro de leitura: {e}")
            return False

class RequisicaoLivro:
    @staticmethod
    def criar(dados):
        """Regista uma nova requisição de livro e marca-o como indisponível."""
        db = get_db()
        import uuid
        try:
            codigo = str(uuid.uuid4().hex[:8]).upper()
            with db.cursor() as cursor:
                # 1. Inserir a requisição (Estado default é 'Pendente' na DB)
                cursor.execute(
                    """INSERT INTO requisicoes_livros (livro_id, nome_aluno, email_aluno, codigo_requisicao)
                       VALUES (?, ?, ?, ?)""",
                    (dados['livro_id'], dados['nome'], dados['email'], codigo)
                )
                # 2. Marcar o livro como indisponível imediatamente
                cursor.execute(
                    "UPDATE livros SET esta_disponivel = 0 WHERE id = ?",
                    (dados['livro_id'],)
                )
            db.commit()
            return codigo
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar requisição de livro: {e}")
            return None

    @staticmethod
    def atualizar_estado(requisicao_id, novo_estado):
        """Atualiza o estado da requisição e a disponibilidade do livro.
        
        Fluxo:
          Pendente → Aceite (código válido 1 dia para levantamento)
          Aceite → Levantado (admin confirma levantamento, 7 dias começam)
          Levantado → Concluido (livro devolvido)
          Pendente/Aceite → Recusado / Expirado (livro volta a ficar disponível)
        """
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT livro_id FROM requisicoes_livros WHERE id = ?", (requisicao_id,))
                res = cursor.fetchone()
                if not res: return False
                livro_id = res['livro_id']

                from datetime import datetime, timedelta

                if novo_estado == 'Aceite':
                    # Admin aprova → código válido por 1 dia
                    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        "UPDATE requisicoes_livros SET estado = ?, data_aprovacao = ? WHERE id = ?",
                        (novo_estado, agora, requisicao_id)
                    )
                elif novo_estado == 'Levantado':
                    # Admin confirma levantamento → 7 dias para devolver
                    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    data_limite = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        "UPDATE requisicoes_livros SET estado = ?, data_levantamento = ?, data_entrega_limite = ? WHERE id = ?",
                        (novo_estado, agora, data_limite, requisicao_id)
                    )
                elif novo_estado in ('Recusado', 'Concluido', 'Expirado'):
                    cursor.execute(
                        "UPDATE requisicoes_livros SET estado = ? WHERE id = ?",
                        (novo_estado, requisicao_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE requisicoes_livros SET estado = ? WHERE id = ?",
                        (novo_estado, requisicao_id)
                    )

                # Disponibilidade do livro
                if novo_estado in ('Recusado', 'Concluido', 'Expirado'):
                    cursor.execute("UPDATE livros SET esta_disponivel = 1 WHERE id = ?", (livro_id,))
                elif novo_estado in ('Aceite', 'Pendente', 'Levantado'):
                    cursor.execute("UPDATE livros SET esta_disponivel = 0 WHERE id = ?", (livro_id,))

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao atualizar estado da requisição: {e}")
            return False

    @staticmethod
    def confirmar_levantamento(codigo):
        """Admin insere o código → se válido e dentro de 1 dia, marca como Levantado."""
        db = get_db()
        from datetime import datetime, timedelta
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """SELECT r.*, l.titulo as livro_titulo
                       FROM requisicoes_livros r
                       LEFT JOIN livros l ON r.livro_id = l.id
                       WHERE r.codigo_requisicao = ? AND r.estado = 'Aceite'""",
                    (codigo.strip().upper(),)
                )
                req = cursor.fetchone()
                if not req:
                    return {'ok': False, 'erro': 'Código inválido ou requisição não está no estado "Aceite".'}

                # Verificar se o código ainda é válido (1 dia desde aprovação)
                data_aprov = req.get('data_aprovacao')
                if data_aprov:
                    if isinstance(data_aprov, str):
                        try:
                            data_aprov = datetime.strptime(data_aprov, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            data_aprov = None
                    if data_aprov and datetime.now() > data_aprov + timedelta(days=1):
                        return {'ok': False, 'erro': 'O código de levantamento expirou (passou mais de 24 horas). A requisição será cancelada.'}

                req_id = req['id']

            # Tudo OK → marcar como Levantado (inicia 7 dias)
            RequisicaoLivro.atualizar_estado(req_id, 'Levantado')
            return {'ok': True, 'requisicao': req}
        except Exception as e:
            print(f"Erro ao confirmar levantamento: {e}")
            return {'ok': False, 'erro': 'Erro interno ao processar o código.'}

    @staticmethod
    def verificar_codigos_expirados():
        """Verifica requisições 'Aceite' cujo código expirou (>1 dia) e reverte o livro."""
        from datetime import datetime, timedelta
        from app.utils.email import EmailService
        db = get_db()
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        expirados = 0

        try:
            with db.cursor() as cursor:
                # Requisições aceites há mais de 1 dia sem levantamento
                limite = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    """SELECT r.*, l.titulo as livro_titulo
                       FROM requisicoes_livros r
                       JOIN livros l ON r.livro_id = l.id
                       WHERE r.estado = 'Aceite' AND r.data_aprovacao IS NOT NULL AND r.data_aprovacao < ?""",
                    (limite,)
                )
                requisicoes = cursor.fetchall()

            for r in requisicoes:
                RequisicaoLivro.atualizar_estado(r['id'], 'Expirado')
                EmailService.enviar_codigo_expirado(
                    r['email_aluno'], r['nome_aluno'], r['livro_titulo']
                )
                expirados += 1
        except Exception as e:
            print(f"Erro ao verificar códigos expirados: {e}")

        return expirados

    @staticmethod
    def verificar_duplicado(livro_id, email):
        """Verifica se o aluno já requisitou este livro e está pendente/aceite."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM requisicoes_livros WHERE livro_id = ? AND email_aluno = ? AND estado IN ('Pendente', 'Aceite', 'Levantado')",
                (livro_id, email)
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_by_livro(livro_id):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM requisicoes_livros WHERE livro_id = ? ORDER BY data_requisicao DESC",
                (livro_id,)
            )
            return cursor.fetchall()

    @staticmethod
    def get_by_id(req_id):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT r.*, r.nome_aluno as nome, r.email_aluno as email, 
                          r.codigo_requisicao as codigo, l.titulo as livro_titulo
                   FROM requisicoes_livros r 
                   LEFT JOIN livros l ON r.livro_id = l.id 
                   WHERE r.id = ?""",
                (req_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def calcular_dias_restantes(data_limite):
        if not data_limite:
            return None
        from datetime import datetime
        if isinstance(data_limite, str):
            try:
                data_limite = datetime.strptime(data_limite, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    data_limite = datetime.strptime(data_limite, '%Y-%m-%d %H:%M')
                except ValueError:
                    return None
        
        hoje = datetime.now()
        delta = data_limite - hoje
        return delta.days + 1 if delta.total_seconds() > 0 else delta.days

    @staticmethod
    def get_ativa_by_livro(livro_id):
        """Retorna a requisição ativa (Pendente, Aceite ou Levantado) para este livro."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM requisicoes_livros WHERE livro_id = ? AND estado IN ('Pendente', 'Aceite', 'Levantado') ORDER BY data_requisicao DESC LIMIT 1",
                (livro_id,)
            )
            res = cursor.fetchone()
            if res:
                res = dict(res)
                res['dias_restantes'] = RequisicaoLivro.calcular_dias_restantes(res.get('data_entrega_limite'))
                return res
            return None

    @staticmethod
    def get_all_paginated(filtros=None, pagina=1, por_pagina=20):
        db = get_db()
        filtros = filtros or {}
        conditions = []
        params = []
        
        if filtros.get('estado'):
            conditions.append("r.estado = ?")
            params.append(filtros['estado'])
            
        if filtros.get('q'):
            conditions.append("(l.titulo LIKE ? OR r.nome_aluno LIKE ?)")
            params.append(f"%{filtros['q']}%")
            params.append(f"%{filtros['q']}%")
            
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        offset = (pagina - 1) * por_pagina
        
        with db.cursor() as cursor:
            # Total
            cursor.execute(f"SELECT COUNT(*) as total FROM requisicoes_livros r LEFT JOIN livros l ON r.livro_id = l.id {where}", params)
            total = cursor.fetchone()['total']
            
            # Página
            cursor.execute(
                f"""SELECT r.*, l.titulo as livro_titulo, l.imagem as livro_imagem 
                   FROM requisicoes_livros r 
                   LEFT JOIN livros l ON r.livro_id = l.id 
                   {where} 
                   ORDER BY r.data_requisicao DESC 
                   LIMIT ? OFFSET ?""",
                params + [por_pagina, offset]
            )
            requisicoes = [dict(row) for row in cursor.fetchall()]
            
            for r in requisicoes:
                r['dias_restantes'] = RequisicaoLivro.calcular_dias_restantes(r.get('data_entrega_limite'))
            
        return requisicoes, total

    @staticmethod
    def enviar_lembretes_devolucao():
        """Procura requisições Levantado que faltam 1 dia para o prazo e envia email."""
        from datetime import datetime, timedelta
        from app.utils.email import EmailService
        db = get_db()
        
        amanha_inicio = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
        amanha_fim = (datetime.now() + timedelta(days=1)).replace(hour=23, minute=59, second=59).strftime('%Y-%m-%d %H:%M:%S')
        
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT r.*, l.titulo as livro_titulo 
                   FROM requisicoes_livros r
                   JOIN livros l ON r.livro_id = l.id
                   WHERE r.estado = 'Levantado' 
                   AND r.data_entrega_limite BETWEEN ? AND ?""",
                (amanha_inicio, amanha_fim)
            )
            requisicoes = cursor.fetchall()
            
            for r in requisicoes:
                EmailService.enviar_lembrete_entrega_livro(
                    r['email_aluno'], 
                    r['nome_aluno'], 
                    r['livro_titulo'], 
                    r['data_entrega_limite']
                )
        return len(requisicoes)
