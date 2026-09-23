from app import get_db
from app.utils.security import sanitize


class Evento:

    @staticmethod
    def get_all(filtros: dict = None, pagina: int = 1, por_pagina: int = 9, apenas_futuros: bool = False):
        db = get_db()
        filtros = filtros or {}
        conditions = ["e.ativo = 1"]
        # Filtrar por data de publicação no frontoffice (apenas_futuros costuma ser True no front)
        if apenas_futuros:
            conditions.append("(e.data_publicacao IS NULL OR e.data_publicacao <= datetime('now', 'localtime'))")
        
        params = []

        # Filtrar apenas eventos futuros (frontoffice)
        if apenas_futuros:
            conditions.append("e.data_evento >= date('now', 'localtime')")

        if filtros.get('q'):
            conditions.append("e.titulo LIKE ?")
            params.append(f"%{filtros['q']}%")
        if filtros.get('cidade'):
            conditions.append("l.cidade LIKE ?")
            params.append(f"%{filtros['cidade']}%")
        if filtros.get('categoria_id'):
            conditions.append("e.categoria_id = ?")
            params.append(int(filtros['categoria_id']))
        if filtros.get('tipo') in ('interno', 'externo'):
            conditions.append("e.tipo = ?")
            params.append(filtros['tipo'])
        if filtros.get('preco_tipo') == 'gratis':
            conditions.append("(e.tipo_ingresso = 'gratis' OR e.preco = 0 OR e.preco IS NULL)")
        elif filtros.get('preco_tipo') == 'pago':
            conditions.append("(e.tipo_ingresso = 'pago' AND e.preco > 0)")
        
        if filtros.get('disponibilidade') == 'disponivel':
            # Subquery para contar inscritos e comparar com limite
            conditions.append("""(e.limite_bilhetes IS NULL OR e.limite_bilhetes > (
                SELECT COUNT(*) FROM inscricoes_eventos WHERE evento_id = e.id
            ))""")

        if filtros.get('data_de'):
            conditions.append("e.data_evento >= ?")
            params.append(filtros['data_de'])
        if filtros.get('data_ate'):
            conditions.append("e.data_evento <= ?")
            params.append(filtros['data_ate'])

        where = " AND ".join(conditions)
        offset = (pagina - 1) * por_pagina

        # Ordenação
        sort_field = filtros.get('ordem', 'data_evento')
        sort_dir = filtros.get('dir', 'ASC')
        
        valid_fields = {
            'data_evento': 'e.data_evento',
            'titulo': 'e.titulo',
            'destaque': 'e.destaque',
            'criado_em': 'e.criado_em',
            'id': 'e.id'
        }
        field = valid_fields.get(sort_field, 'e.data_evento')
        direction = 'ASC' if sort_dir.upper() == 'ASC' else 'DESC'

        with db.cursor() as cursor:
            cursor.execute(
                f"""SELECT COUNT(*) as total 
                    FROM eventos e 
                    LEFT JOIN locais l ON e.local_id = l.id
                    WHERE {where}""",
                params
            )
            total = cursor.fetchone()['total']

            cursor.execute(
                f"""SELECT e.*, c.nome AS categoria_nome, c.icone AS categoria_icone, c.cor AS categoria_cor,
                           l.nome AS local, l.cidade AS cidade, l.morada AS local_morada, l.capacidade AS local_capacidade
                    FROM eventos e
                    LEFT JOIN categorias c ON e.categoria_id = c.id
                    LEFT JOIN locais l ON e.local_id = l.id
                    WHERE {where}
                    ORDER BY {field} {direction}
                    LIMIT ? OFFSET ?""",
                params + [por_pagina, offset]
            )
            return cursor.fetchall(), total

    @staticmethod
    def get_by_id(evento_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT e.*, c.nome AS categoria_nome, c.icone AS categoria_icone, c.cor AS categoria_cor,
                           l.nome AS local, l.cidade AS cidade, l.morada AS local_morada, l.capacidade AS local_capacidade
                   FROM eventos e
                    LEFT JOIN categorias c ON e.categoria_id = c.id
                    LEFT JOIN locais l ON e.local_id = l.id
                    WHERE e.id = ? AND e.ativo = 1""",
                 (evento_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def get_destaques(limite: int = 3):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT e.*, c.nome AS categoria_nome, c.icone AS categoria_icone, c.cor AS categoria_cor,
                           l.nome AS local, l.cidade AS cidade
                   FROM eventos e
                   LEFT JOIN categorias c ON e.categoria_id = c.id
                   LEFT JOIN locais l ON e.local_id = l.id
                   WHERE e.ativo = 1 AND e.destaque = 1
                   AND e.data_evento >= date('now', 'localtime')
                   AND (e.data_publicacao IS NULL OR e.data_publicacao <= datetime('now', 'localtime'))
                   ORDER BY e.data_evento ASC LIMIT ?""",
                (limite,)
            )
            return cursor.fetchall()

    @staticmethod
    def toggle_destaque(evento_id: int) -> bool:
        """Alterna o estado de destaque de um evento (0 -> 1 ou 1 -> 0)."""
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE eventos SET destaque = CASE WHEN destaque = 1 THEN 0 ELSE 1 END WHERE id = ?",
                    (evento_id,)
                )
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def get_cidades():
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT l.cidade FROM eventos e JOIN locais l ON e.local_id = l.id WHERE e.ativo = 1 ORDER BY l.cidade"
            )
            return [row['cidade'] for row in cursor.fetchall()]

    @staticmethod
    def _resolver_local(dados: dict):
        """Traduz local e cidade em local_id, criando se não existir."""
        if dados.get('local_id'):
            try:
                return int(dados['local_id'])
            except (ValueError, TypeError):
                pass
            
        nome_local = sanitize(dados.get('local', ''))
        cidade = sanitize(dados.get('cidade', 'Vila Nova de Gaia'))
        
        if not nome_local and not cidade:
            return None
            
        db = get_db()
        with db.cursor() as cursor:
            # Tentar encontrar local existente com mesmo nome e cidade
            cursor.execute(
                "SELECT id FROM locais WHERE nome = ? AND cidade = ?",
                (nome_local, cidade)
            )
            res = cursor.fetchone()
            if res:
                return res['id']
            
            # Criar novo local
            cursor.execute(
                "INSERT INTO locais (nome, cidade) VALUES (?, ?)",
                (nome_local, cidade)
            )
            # Nota: O commit será feito pelo método que chama este helper
            return cursor.lastrowid

    @staticmethod
    def criar(dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                local_id = Evento._resolver_local(dados)
                # Determinar preço: 0 se grátis
                tipo_ingresso = dados.get('tipo_ingresso', 'gratis')
                
                # Preço: converter com segurança
                preco_raw = dados.get('preco')
                try:
                    preco = float(preco_raw) if preco_raw and tipo_ingresso == 'pago' else 0.00
                except (ValueError, TypeError):
                    preco = 0.00
                    
                # Limite: converter com segurança
                limite_raw = dados.get('limite_bilhetes')
                limite = None
                if limite_raw and str(limite_raw).strip():
                    try:
                        limite = int(limite_raw)
                    except (ValueError, TypeError):
                        limite = None
                
                # Data de publicação: tratar checkbox de agendamento
                if not dados.get('usar_agendamento'):
                    data_pub = None
                else:
                    data_pub = dados.get('data_publicacao')
                    if data_pub and not str(data_pub).strip():
                        data_pub = None

                cursor.execute(
                    """INSERT INTO eventos (titulo, descricao, data_evento, hora, local_id, tipo,
                       categoria_id, link_externo, link_bilheteira, destaque, imagem,
                       tipo_ingresso, preco, limite_bilhetes, data_publicacao)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('descricao', '')),
                        dados.get('data_evento') or None,
                        dados.get('hora') or None,
                        local_id,
                        dados.get('tipo', 'externo'),
                        dados.get('categoria_id') or None,
                        sanitize(dados.get('link_externo', '')),
                        sanitize(dados.get('link_bilheteira', '')),
                        1 if dados.get('destaque') else 0,
                        dados.get('imagem'),
                        tipo_ingresso,
                        preco,
                        limite,
                        data_pub
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao criar evento: {e}")
            return False

    @staticmethod
    def editar(evento_id: int, dados: dict) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                local_id = Evento._resolver_local(dados)
                tipo_ingresso = dados.get('tipo_ingresso', 'gratis')
                
                # Preço: converter com segurança
                preco_raw = dados.get('preco')
                try:
                    preco = float(preco_raw) if preco_raw and tipo_ingresso == 'pago' else 0.00
                except (ValueError, TypeError):
                    preco = 0.00
                    
                # Limite: converter com segurança
                limite_raw = dados.get('limite_bilhetes')
                limite = None
                if limite_raw and str(limite_raw).strip():
                    try:
                        limite = int(limite_raw)
                    except (ValueError, TypeError):
                        limite = None
                
                # Data de publicação: tratar checkbox de agendamento
                if not dados.get('usar_agendamento'):
                    data_pub = None
                else:
                    data_pub = dados.get('data_publicacao')
                    if data_pub and not str(data_pub).strip():
                        data_pub = None

                cursor.execute(
                    """UPDATE eventos SET titulo=?, descricao=?, data_evento=?, hora=?,
                       local_id=?, tipo=?, categoria_id=?, link_externo=?, link_bilheteira=?, destaque=?, imagem=?,
                       tipo_ingresso=?, preco=?, limite_bilhetes=?, data_publicacao=?
                       WHERE id=?""",
                    (
                        sanitize(dados.get('titulo', '')),
                        sanitize(dados.get('descricao', '')),
                        dados.get('data_evento') or None,
                        dados.get('hora') or None,
                        local_id,
                        dados.get('tipo', 'externo'),
                        dados.get('categoria_id') or None,
                        sanitize(dados.get('link_externo', '')),
                        sanitize(dados.get('link_bilheteira', '')),
                        1 if dados.get('destaque') else 0,
                        dados.get('imagem'),
                        tipo_ingresso,
                        preco,
                        limite,
                        data_pub,
                        evento_id
                    )
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Erro ao editar evento: {e}")
            return False

    @staticmethod
    def eliminar(evento_id: int) -> bool:
        db = get_db()
        try:
            with db.cursor() as cursor:
                cursor.execute("UPDATE eventos SET ativo = 0 WHERE id = ?", (evento_id,))
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False

    # ── Bilheteira / Inscrições em Eventos ──────────────────────

    @staticmethod
    def contar_inscritos(evento_id: int) -> int:
        """Conta o número de inscrições/bilhetes vendidos para um evento."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM inscricoes_eventos WHERE evento_id = ?",
                (evento_id,)
            )
            return cursor.fetchone()['total']

    @staticmethod
    def inscrever(evento_id: int, nome: str, email: str) -> dict:
        """Processa uma inscrição/compra de bilhete para um evento.
        Retorna {'ok': True, 'codigo': ...} ou {'ok': False, 'erro': ...}
        """
        import uuid
        db = get_db()
        try:
            evento = Evento.get_by_id(evento_id)
            if not evento:
                return {'ok': False, 'erro': 'Evento não encontrado.'}

            # Verificar limite de bilhetes (stock)
            if evento.get('limite_bilhetes'):
                inscritos = Evento.contar_inscritos(evento_id)
                if inscritos >= evento['limite_bilhetes']:
                    return {'ok': False, 'erro': 'Evento Esgotado — já não existem bilhetes disponíveis.'}

            # Determinar valor
            valor = float(evento.get('preco') or 0) if evento.get('tipo_ingresso') == 'pago' else 0.00
            codigo = str(uuid.uuid4().hex[:8]).upper()

            with db.cursor() as cursor:
                # Verificar se o utilizador já está inscrito neste evento
                cursor.execute(
                    "SELECT id FROM inscricoes_eventos WHERE evento_id = ? AND email = ?",
                    (evento_id, email.lower())
                )
                if cursor.fetchone():
                    return {'ok': False, 'erro': 'Já se encontra inscrito neste evento com este e-mail.'}

                cursor.execute(
                    """INSERT INTO inscricoes_eventos (evento_id, nome, email, codigo, valor_pago)
                       VALUES (?, ?, ?, ?, ?)""",
                    (evento_id, sanitize(nome), email.lower(), codigo, valor)
                )
            db.commit()
            return {'ok': True, 'codigo': codigo}
        except Exception as e:
            db.rollback()
            print(f"Erro ao inscrever em evento: {e}")
            return {'ok': False, 'erro': 'Erro interno ao processar inscrição.'}
    @staticmethod
    def get_galeria(evento_id: int):
        """Retorna todas as fotos da galeria de um evento específico."""
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM galeria_eventos WHERE evento_id = ? AND ativo = 1 ORDER BY criado_em DESC",
                (evento_id,)
            )
            return cursor.fetchall()
