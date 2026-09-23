from flask import Blueprint, jsonify, request, current_app
from app.models.evento import Evento
from app.models.livro import Livro
from app.models.espetaculo import Espetaculo
from datetime import date, datetime, time, timedelta

api_bp = Blueprint('api', __name__)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.strftime('%H:%M')
    raise TypeError ("Type ? not serializable" % type(obj))

@api_bp.route('/v1/eventos')
def get_eventos():
    """API para listar eventos com filtros."""
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 9, type=int)
    
    # Construir dicionário de filtros (réplica da lógica do frontoffice.py)
    filtros = {}
    q = request.args.get('q', '').strip()
    cidade = request.args.get('cidade', '').strip()
    cat_id = request.args.get('categoria_id', '').strip()
    tipo = request.args.get('tipo', '').strip()
    disp = request.args.get('disponibilidade', '').strip()
    data_de = request.args.get('data_de', '').strip()
    data_ate = request.args.get('data_ate', '').strip()

    if q and q != '': 
        filtros['q'] = q
    if cidade and cidade != '' and cidade != '0': 
        filtros['cidade'] = cidade
    if cat_id and cat_id.isdigit() and int(cat_id) > 0: 
        filtros['categoria_id'] = int(cat_id)
    if tipo in ('interno', 'externo'): 
        filtros['tipo'] = tipo
    if disp == 'disponivel': 
        filtros['disponibilidade'] = disp
    
    # Datas
    if data_de:
        filtros['data_de'] = data_de
        if not data_ate: filtros['data_ate'] = data_de
    if data_ate:
        filtros['data_ate'] = data_ate
    
    try:
        eventos, total = Evento.get_all(filtros, pagina, por_pagina, apenas_futuros=True)
        
        # Converter objetos de data/hora para string e adicionar inscritos
        for ev in eventos:
            # Adicionar contagem de inscritos para o front-end calcular disponibilidade
            ev['inscritos'] = Evento.contar_inscritos(ev['id'])
            
            for key, value in ev.items():
                if isinstance(value, (datetime, date)):
                    ev[key] = value.isoformat()
                elif isinstance(value, time):
                    ev[key] = value.strftime('%H:%M')
                elif isinstance(value, timedelta):
                    # Converter timedelta (comum em campos TIME no MySQL) para HH:MM
                    total_seconds = int(value.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    ev[key] = f"{hours:02d}:{minutes:02d}"
                    
        return jsonify({
            'eventos': eventos,
            'total': total,
            'pagina': pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/biblioteca')
def get_biblioteca():
    """API para listar livros com filtros."""
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 12, type=int)
    
    # Construir dicionário apenas com filtros que têm valor
    filtros = {}
    for arg in ['q', 'genero', 'disponibilidade']:
        val = request.args.get(arg, '').strip()
        if val:
            filtros[arg] = val
    
    try:
        livros, total = Livro.get_all_paginated(filtros, pagina, por_pagina)
        
        # Formatar campos se necessário (Livro costuma ter apenas strings e ints, mas por segurança)
        for livro in livros:
            for key, value in livro.items():
                if isinstance(value, (datetime, date)):
                    livro[key] = value.isoformat()
                elif isinstance(value, timedelta):
                    total_seconds = int(value.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    livro[key] = f"{hours:02d}:{minutes:02d}"
                    
        return jsonify({
            'livros': livros,
            'total': total,
            'pagina': pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/categorias')
def get_categorias():
    """API para obter todas as categorias."""
    from app.models.categoria import Categoria
    try:
        categorias = Categoria.get_all()
        return jsonify(categorias)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/eventos/<int:evento_id>/disponibilidade')
def get_disponibilidade_evento(evento_id):
    """API para obter a disponibilidade real de um evento específico."""
    try:
        evento = Evento.get_by_id(evento_id)
        if not evento:
            return jsonify({'error': 'Evento não encontrado'}), 404
            
        inscritos = Evento.contar_inscritos(evento_id)
        limite = evento.get('limite_bilhetes')
        
        vagas_restantes = None
        disponivel = True
        
        if limite is not None:
            vagas_restantes = max(0, limite - inscritos)
            disponivel = vagas_restantes > 0
            
        return jsonify({
            'evento_id': evento_id,
            'vagas_totais': limite,
            'inscritos': inscritos,
            'vagas_restantes': vagas_restantes,
            'disponivel': disponivel
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/teatro/<int:esp_id>/disponibilidade')
def get_disponibilidade_teatro(esp_id):
    """API para obter a disponibilidade real de um espetáculo de teatro."""
    try:
        from app.models.espetaculo import Espetaculo
        from app.models.inscricao_teatro import InscricaoTeatro
        
        esp = Espetaculo.get_by_id(esp_id)
        if not esp:
            return jsonify({'error': 'Espetáculo não encontrado'}), 404
            
        ocupados = Espetaculo.contar_inscritos(esp_id)
        
        # Cálculo de lotação: Filas * 12 lugares por fila (configuração padrão do mapa)
        limite_filas = esp.get('limite_filas', 8)
        lotacao_total = limite_filas * 12
        
        vagas_restantes = max(0, lotacao_total - ocupados)
        
        return jsonify({
            'espetaculo_id': esp_id,
            'vagas_totais': lotacao_total,
            'inscritos': ocupados,
            'vagas_restantes': vagas_restantes,
            'disponivel': vagas_restantes > 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/validar-email', methods=['POST'])
def validar_email():
    """API para validar se um e-mail é institucional e identificar o tipo."""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        evento_id = data.get('evento_id')
        
        if not email:
            return jsonify({'valido': False, 'mensagem': 'E-mail não fornecido'}), 400
            
        if not email.endswith('@ispgaya.pt'):
            return jsonify({
                'valido': False, 
                'mensagem': 'Apenas e-mails institucionais (@ispgaya.pt) são permitidos.'
            })
            
        # Verificar duplicado se houver evento_id
        if evento_id:
            from app import get_db
            db = get_db()
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM inscricoes_eventos WHERE evento_id = ? AND email = ?",
                    (evento_id, email)
                )
                if cursor.fetchone():
                    return jsonify({
                        'valido': False,
                        'mensagem': 'Este e-mail já está inscrito neste evento.'
                    })

        # Verificar duplicado se houver espetaculo_id
        if espetaculo_id := data.get('espetaculo_id'):
            from app import get_db
            db = get_db()
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM inscricoes_teatro WHERE espetaculo_id = ? AND email_aluno = ?",
                    (espetaculo_id, email)
                )
                if cursor.fetchone():
                    return jsonify({
                        'valido': False,
                        'mensagem': 'Este e-mail já tem uma reserva para este espetáculo.'
                    })
            
        # Lógica extra: identificar se é aluno
        # Exemplo: ispg2023103434@ispgaya.pt
        import re
        is_aluno = re.match(r'^[a-z]{4}\d+@ispgaya\.pt$', email)
        
        return jsonify({
            'valido': True,
            'tipo': 'aluno' if is_aluno else 'docente/staff',
            'mensagem': 'E-mail institucional válido.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/backoffice/stats')
def get_dashboard_stats():
    """API para obter estatísticas completas para o dashboard do backoffice."""
    try:
        from app import get_db
        from app.models.evento import Evento
        from app.models.livro import Livro
        from app.models.utilizador import Utilizador
        from app.models.clube import Clube
        
        db = get_db()
        stats = {}
        
        with db.cursor() as cursor:
            # 1. Contagens Gerais
            cursor.execute("SELECT COUNT(*) as total FROM eventos WHERE ativo = 1")
            stats['total_eventos'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM livros")
            stats['total_livros'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM utilizadores WHERE ativo = 1")
            stats['total_utilizadores'] = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM clubes WHERE ativo = 1")
            stats['total_clubes'] = cursor.fetchone()['total']
            
            # 2. Inscrições por Mês (Últimos 6 meses - Garantir escala completa)
            cursor.execute("""
                SELECT strftime('%Y-%m', data_inscricao) as mes, COUNT(*) as total
                FROM (
                    SELECT criado_em as data_inscricao FROM inscricoes_eventos
                    UNION ALL
                    SELECT data_inscricao FROM inscricoes_teatro
                ) combined
                WHERE data_inscricao >= date('now', 'localtime', '-6 months')
                GROUP BY mes
                ORDER BY mes ASC
            """)
            db_results = {row['mes']: row['total'] for row in cursor.fetchall()}
            
            # Gerar lista dos últimos 6 meses
            stats['inscricoes_mensais'] = []
            today = date.today()
            for i in range(5, -1, -1):
                # Subtrair i meses logicamente
                month = today.month - i
                year = today.year
                while month <= 0:
                    month += 12
                    year -= 1
                
                mes_str = f"{year}-{month:02d}"
                stats['inscricoes_mensais'].append({
                    'mes': mes_str,
                    'total': db_results.get(mes_str, 0)
                })
            
            # 3. Distribuição por Categoria
            cursor.execute("""
                SELECT c.nome, COUNT(e.id) as total
                FROM categorias c
                LEFT JOIN eventos e ON e.categoria_id = c.id AND e.ativo = 1
                GROUP BY c.id, c.nome
                HAVING total > 0
            """)
            stats['categorias_distribuicao'] = cursor.fetchall()
            
            # 4. Top 5 Eventos Populares
            cursor.execute("""
                SELECT e.titulo, COUNT(i.id) as inscritos
                FROM eventos e
                JOIN inscricoes_eventos i ON i.evento_id = e.id
                WHERE e.ativo = 1
                GROUP BY e.id, e.titulo
                ORDER BY inscritos DESC
                LIMIT 5
            """)
            stats['top_eventos'] = cursor.fetchall()

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/autocomplete')
def autocomplete():
    """API para sugestões de pesquisa (autocomplete)."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
        
    tipo_filtro = request.args.get('tipo', '').lower()
        
    try:
        from app import get_db
        db = get_db()
        sugestoes = []
        
        with db.cursor() as cursor:
            # Sugestões de Eventos (Se não filtrado por livro ou teatro)
            if tipo_filtro not in ('livro', 'teatro'):
                cursor.execute("""
                    SELECT id, titulo, 'evento' as tipo 
                    FROM eventos 
                    WHERE titulo LIKE ? AND ativo = 1 
                    AND data_evento >= date('now', 'localtime')
                    AND (data_publicacao IS NULL OR data_publicacao <= datetime('now', 'localtime'))
                    LIMIT 5
                """, (f'%{q}%',))
                sugestoes.extend(cursor.fetchall())
            
            # Sugestões de Teatro (Se não filtrado por livro ou evento)
            if tipo_filtro not in ('livro', 'evento'):
                cursor.execute("""
                    SELECT id, titulo, 'teatro' as tipo 
                    FROM espetaculos 
                    WHERE titulo LIKE ? AND ativo = 1 
                    AND data_evento >= date('now', 'localtime')
                    AND (data_publicacao IS NULL OR data_publicacao <= datetime('now', 'localtime'))
                    LIMIT 5
                """, (f'%{q}%',))
                sugestoes.extend(cursor.fetchall())

            # Sugestões de Livros (Se não filtrado por evento ou teatro)
            if tipo_filtro not in ('evento', 'teatro', 'noticia'):
                cursor.execute("""
                    SELECT id, titulo, 'livro' as tipo 
                    FROM livros 
                    WHERE titulo LIKE ? 
                    LIMIT 5
                """, (f'%{q}%',))
                sugestoes.extend(cursor.fetchall())
            
            # Sugestões de Notícias
            if tipo_filtro in ('noticia', 'all'):
                cursor.execute("""
                    SELECT id, titulo, 'noticia' as tipo 
                    FROM noticias 
                    WHERE titulo LIKE ? AND ativo = 1 
                    LIMIT 5
                """, (f'%{q}%',))
                sugestoes.extend(cursor.fetchall())
            
        return jsonify(sugestoes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/backoffice/requisicoes/stats')
def get_requisicoes_stats():
    """API para estatísticas de requisições de livros."""
    try:
        from app import get_db
        db = get_db()
        stats = {}
        
        with db.cursor() as cursor:
            # 1. Requisições por dia (últimos 30 dias)
            cursor.execute("""
                SELECT DATE(data_requisicao) as dia, COUNT(*) as total
                FROM requisicoes_livros
                WHERE data_requisicao >= date('now', 'localtime', '-30 days')
                GROUP BY dia
                ORDER BY dia ASC
            """)
            db_dias = {str(row['dia']): row['total'] for row in cursor.fetchall()}
            
            # Preencher dias sem dados com 0
            stats['por_dia'] = []
            today = date.today()
            for i in range(29, -1, -1):
                d = today - timedelta(days=i)
                d_str = d.isoformat()
                stats['por_dia'].append({
                    'dia': d.strftime('%d/%m'),
                    'total': db_dias.get(d_str, 0)
                })
            
            # 2. Distribuição por estado
            cursor.execute("""
                SELECT estado, COUNT(*) as total
                FROM requisicoes_livros
                GROUP BY estado
            """)
            stats['por_estado'] = cursor.fetchall()
            
            # 3. Top livros mais requisitados
            cursor.execute("""
                SELECT l.titulo, COUNT(r.id) as total
                FROM requisicoes_livros r
                JOIN livros l ON r.livro_id = l.id
                GROUP BY r.livro_id, l.titulo
                ORDER BY total DESC
                LIMIT 5
            """)
            stats['top_livros'] = cursor.fetchall()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/v1/teatro')
def get_teatro():
    """API para listar espetáculos de teatro com filtros."""
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 6, type=int)
    
    filtros = {
        'apenas_publicados': True,
        'apenas_futuros': True
    }
    
    # Capturar argumentos (Removido classificacao_etaria)
    for arg in ['q', 'tipo', 'entrada', 'data_de', 'data_ate', 'destaque']:
        val = request.args.get(arg, '').strip()
        if val:
            filtros[arg] = val
            
    try:
        espetaculos, total = Espetaculo.get_all_paginated(filtros, pagina, por_pagina)
        
        # Formatar datas e adicionar inscritos
        for esp in espetaculos:
            esp['inscritos'] = Espetaculo.contar_inscritos(esp['id'])
            for key, value in esp.items():
                if isinstance(value, (datetime, date)):
                    esp[key] = value.isoformat()
                elif isinstance(value, time):
                    esp[key] = value.strftime('%H:%M')
                elif isinstance(value, timedelta):
                    total_seconds = int(value.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    esp[key] = f"{hours:02d}:{minutes:02d}"
                    
        return jsonify({
            'agenda': espetaculos,
            'total': total,
            'pagina': pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/v1/cidades')

def get_cidades():
    """API para obter todas as cidades com eventos."""
    try:
        cidades = Evento.get_cidades()
        return jsonify(cidades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/v1/noticias')
def get_noticias():
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = request.args.get('por_pagina', 9, type=int)
    filtros = {}
    q = request.args.get('q', '').strip()
    cat_id = request.args.get('categoria_id', '').strip()
    data_de = request.args.get('data_de', '').strip()
    data_ate = request.args.get('data_ate', '').strip()

    if q: filtros['q'] = q
    if cat_id and cat_id.isdigit(): filtros['categoria_id'] = int(cat_id)
    if data_de: filtros['data_de'] = data_de
    if data_ate: filtros['data_ate'] = data_ate

    try:
        from app.models.noticia import Noticia
        noticias, total = Noticia.get_all(filtros, pagina, por_pagina)
        for n in noticias:
            for key, value in n.items():
                if isinstance(value, (datetime, date)):
                    n[key] = value.isoformat()
        return jsonify({'noticias': noticias, 'total': total, 'pagina': pagina, 'total_paginas': (total + por_pagina - 1) // por_pagina})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def obter_resposta_gemini(api_key, mensagem, historico=None):
    import urllib.request
    import urllib.error
    import json
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    system_instruction = (
        "És o Assistente Virtual do website Laboratório Cultural do ISPGAYA (Instituto Superior Politécnico Gaya).\n"
        "O teu objetivo é ajudar os utilizadores a esclarecer dúvidas sobre os nossos clubes (Teatro, Tuna Académica e Biblioteca/Leitura), eventos e requisição de livros.\n\n"
        "Informações sobre o Laboratório Cultural:\n"
        "1. Clube de Teatro:\n"
        "   - Oferece ensaios semanais, espetáculos e reservas de bilhetes online com mapa de sala interativo.\n"
        "   - Para inscrever-se no Clube de Teatro (como membro), o utilizador deve aceder a: /lab-cultural/clube-teatro/juntar\n"
        "   - Página principal do Teatro: /lab-cultural/clube-teatro\n"
        "   - Galeria do Teatro: /lab-cultural/clube-teatro/galeria\n\n"
        "2. Tuna Académica:\n"
        "   - Grupo musical e académico do ISPGAYA. Atua em eventos académicos e festivais.\n"
        "   - Para juntar-se à Tuna, aceder a: /lab-cultural/tuna/juntar\n"
        "   - Página da Tuna: /lab-cultural/tuna\n"
        "   - Galeria da Tuna: /lab-cultural/tuna/galeria\n\n"
        "3. Clube de Leitura e Biblioteca:\n"
        "   - Permite consultar e requisitar livros do catálogo do laboratório de forma 100% virtual.\n"
        "   - Para fazer parte do Clube de Leitura (receber novidades de debates e encontros), aceder a: /lab-cultural/clube-leitura/juntar\n"
        "   - Página da Biblioteca: /biblioteca\n\n"
        "4. Eventos e Agenda:\n"
        "   - Temos palestras, workshops e conferências.\n"
        "   - Página de Eventos: /eventos\n\n"
        "Regras importantes de resposta:\n"
        "- Responde em Português de Portugal de forma simpática, clara, concisa e profissional.\n"
        "- O utilizador pode cometer pequenos erros de digitação (ex: \"increver\" em vez de \"inscrever\", \"teatru\", \"tunaa\"), deves perceber a sua intenção e responder com naturalidade.\n"
        "- Sempre que indicares caminhos ou links de páginas do site (ex: /lab-cultural/clube-teatro/juntar, /biblioteca, /eventos, etc.), deves OBRIGATORIAMENTE formatá-los como links em Markdown com um texto descritivo. Exemplo: [Inscrição no Clube de Teatro](/lab-cultural/clube-teatro/juntar) ou [Página da Biblioteca](/biblioteca). NUNCA escrevas o caminho puro (como /biblioteca) no texto da resposta.\n"
        "- Nunca inventes informações que não constam acima. Se não souberes a resposta, aconselha o utilizador a deixar uma mensagem usando a opção \"Enviar Mensagem\" para falarmos com a equipa de suporte.\n"
        "- Devolve a tua resposta em formato de texto limpo (Markdown simples sem exagerar nos negritos)."
    )
    
    contents = []
    if historico and isinstance(historico, list):
        for turn in historico:
            if isinstance(turn, dict) and 'role' in turn and 'parts' in turn:
                role = 'user' if turn['role'] == 'user' else 'model'
                parts = []
                for p in turn['parts']:
                    if isinstance(p, dict) and 'text' in p:
                        parts.append({"text": p['text']})
                if parts:
                    contents.append({"role": role, "parts": parts})
                    
    if not contents or contents[-1].get("role") != "user":
        contents.append({
            "role": "user",
            "parts": [{"text": mensagem}]
        })
        
    payload = {
        "systemInstruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 2000
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        import ssl
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=8, context=context) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return None
    except Exception as e:
        print(f"Erro ao contactar o Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None


@api_bp.route('/v1/chatbot', methods=['POST'])
def chatbot_responder():
    """Processa mensagens enviadas ao chatbot e devolve respostas estruturadas."""
    import unicodedata
    
    def normalizar_texto(texto):
        if not texto:
            return ""
        # Remover acentos e converter para minúsculas
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
        return texto.strip().lower()

    try:
        data = request.get_json() or {}
        mensagem_original = data.get('message', '').strip()
        msg_norm = normalizar_texto(mensagem_original)
        historico = data.get('history', [])
        
        resposta = ""
        sugestoes = []
        
        # Tentar obter resposta via API do Gemini se configurado
        api_key = current_app.config.get('GEMINI_API_KEY')
        resposta_ai = None
        if api_key:
            resposta_ai = obter_resposta_gemini(api_key, mensagem_original, historico=historico)
            
        if resposta_ai:
            resposta = resposta_ai
            # Gerar sugestões baseadas no conteúdo da resposta
            if "/lab-cultural/clube-teatro/juntar" in resposta:
                sugestoes.append({"label": "📝 Inscrição Teatro", "link": "/lab-cultural/clube-teatro/juntar"})
            if "/lab-cultural/tuna/juntar" in resposta:
                sugestoes.append({"label": "🎶 Inscrição Tuna", "link": "/lab-cultural/tuna/juntar"})
            if "/lab-cultural/clube-leitura/juntar" in resposta:
                sugestoes.append({"label": "📚 Inscrição Leitura", "link": "/lab-cultural/clube-leitura/juntar"})
            
            if "/lab-cultural/clube-teatro" in resposta and not any(s.get("link") == "/lab-cultural/clube-teatro" for s in sugestoes):
                sugestoes.append({"label": "🎭 Ver Teatro", "link": "/lab-cultural/clube-teatro"})
            if "/lab-cultural/tuna" in resposta and not any(s.get("link") == "/lab-cultural/tuna" for s in sugestoes):
                sugestoes.append({"label": "🎶 Ver Tuna", "link": "/lab-cultural/tuna"})
            if "/biblioteca" in resposta:
                sugestoes.append({"label": "📚 Catálogo Livros", "link": "/biblioteca"})
            if "/eventos" in resposta:
                sugestoes.append({"label": "📅 Agenda Eventos", "link": "/eventos"})
                
            if "enviar mensagem" in resposta.lower() or "suporte" in resposta.lower() or "mensagem" in resposta.lower():
                sugestoes.append({"label": "✉️ Enviar Mensagem", "text": "Enviar Mensagem"})
                
            sugestoes.append({"label": "🚪 Voltar ao Menu", "text": "Olá"})
        else:
            # Fallback para o motor de regras locais inteligente
            # 1. Saudações
            if any(keyword in msg_norm for keyword in ["ola", "oi", "bom dia", "boa tarde", "boa noite", "saudacoes", "hey", "como estas", "tudo bem"]):
                resposta = (
                    "Olá! Sou o Assistente Virtual do Laboratório Cultural do ISPGAYA. "
                    "Estou aqui para ajudar-te com informações sobre eventos, espetáculos de teatro, a nossa tuna ou a biblioteca."
                )
                sugestoes = [
                    {"label": "🎭 Clube de Teatro", "text": "Teatro"},
                    {"label": "📚 Biblioteca & Livros", "text": "Biblioteca"},
                    {"label": "🎶 Tuna Académica", "text": "Tuna"},
                    {"label": "✉️ Enviar Mensagem", "text": "Enviar Mensagem"}
                ]
                
            # 2. Inscrições nos Clubes
            elif any(keyword in msg_norm for keyword in ["inscrever", "inscricao", "inscricoes", "increver", "incricao", "incricoes", "participar", "juntar", "entrar", "fazer parte", "quero ser", "quero pertencer", "candidatar", "recrutamento", "aderir", "inscrevo"]):
                # Sub-analisar qual é o clube
                if any(k in msg_norm for k in ["teatro", "palco", "peca", "espetaculo"]):
                    resposta = (
                        "Queres inscrever-te no **Clube de Teatro**? Excelente escolha! "
                        "Podes preencher a tua ficha de inscrição diretamente na página do clube."
                    )
                    sugestoes = [
                        {"label": "📝 Inscrição Teatro", "link": "/lab-cultural/clube-teatro/juntar"},
                        {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                    ]
                elif any(k in msg_norm for k in ["tuna", "musica", "cantar", "tuno"]):
                    resposta = (
                        "Gostavas de juntar-te à **Tuna Académica** do ISPGAYA? "
                        "O recrutamento está sempre aberto para novos talentos! Podes fazer a tua pré-inscrição online."
                    )
                    sugestoes = [
                        {"label": "🎶 Inscrição Tuna", "link": "/lab-cultural/tuna/juntar"},
                        {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                    ]
                elif any(k in msg_norm for k in ["leitura", "livro", "livros", "ler", "biblioteca"]):
                    resposta = (
                        "Gostavas de participar no **Clube de Leitura**? As inscrições estão abertas! "
                        "Preenche o formulário online para receberes as novidades das próximas sessões e debates."
                    )
                    sugestoes = [
                        {"label": "📚 Inscrição Leitura", "link": "/lab-cultural/clube-leitura/juntar"},
                        {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                    ]
                else:
                    resposta = (
                        "Gostavas de fazer parte de algum dos nossos clubes e atividades do Laboratório Cultural? "
                        "Escolhe em qual te pretendes inscrever:"
                    )
                    sugestoes = [
                        {"label": "🎭 Juntar-se ao Teatro", "link": "/lab-cultural/clube-teatro/juntar"},
                        {"label": "🎶 Juntar-se à Tuna", "link": "/lab-cultural/tuna/juntar"},
                        {"label": "📚 Juntar-se à Leitura", "link": "/lab-cultural/clube-leitura/juntar"},
                        {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                    ]

            # 3. Teatro
            elif any(keyword in msg_norm for keyword in ["teatro", "peca", "espetaculo", "ensaios", "reserva", "reservar", "bilhete", "bilhetes", "lugar", "lugares"]):
                resposta = (
                    "O Clube de Teatro do ISPGAYA promove ensaios semanais e produções incríveis! "
                    "Na secção de Teatro do site, podes consultar a nossa agenda de espetáculos e reservar os teus bilhetes "
                    "escolhendo diretamente a tua cadeira no nosso mapa interativo da sala."
                )
                sugestoes = [
                    {"label": "📅 Ver Agenda Teatro", "link": "/lab-cultural/clube-teatro"},
                    {"label": "📸 Galeria do Teatro", "link": "/lab-cultural/clube-teatro/galeria"},
                    {"label": "📝 Inscrição no Clube", "link": "/lab-cultural/clube-teatro/juntar"},
                    {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                ]
                
            # 4. Tuna
            elif any(keyword in msg_norm for keyword in ["tuna", "musica", "atuacao", "atuacoes", "pandeireta", "estudantina", "tuno", "tunas"]):
                resposta = (
                    "A Tuna Académica do ISPGAYA enche de música e alegria a nossa instituição! "
                    "Podes ver as próximas atuações da Tuna na sua secção e recordar momentos passados na galeria de fotos."
                )
                sugestoes = [
                    {"label": "🎶 Ver Página da Tuna", "link": "/lab-cultural/tuna"},
                    {"label": "📸 Galeria da Tuna", "link": "/lab-cultural/tuna/galeria"},
                    {"label": "📝 Inscrição na Tuna", "link": "/lab-cultural/tuna/juntar"},
                    {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                ]
                
            # 5. Biblioteca / Livros
            elif any(keyword in msg_norm for keyword in ["livro", "livros", "biblioteca", "requisitar", "devolver", "prazo", "emprestimo"]):
                resposta = (
                    "Na nossa Biblioteca Virtual podes consultar todo o catálogo de livros disponíveis no Laboratório. "
                    "Para fazeres uma requisição, basta clicares em 'Requisitar' no livro pretendido e introduzir o teu e-mail institucional."
                )
                sugestoes = [
                    {"label": "📚 Ir para a Biblioteca", "link": "/biblioteca"},
                    {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                ]
                
            # 6. Eventos
            elif any(keyword in msg_norm for keyword in ["evento", "eventos", "agenda", "atividades", "palestra", "workshop", "conferencia"]):
                resposta = (
                    "Temos sempre várias palestras, workshops e eventos culturais a acontecer! "
                    "Visita a nossa Agenda de Eventos geral para descobrires o que está planeado e fazeres a tua inscrição."
                )
                sugestoes = [
                    {"label": "📅 Ver Eventos", "link": "/eventos"},
                    {"label": "🚪 Voltar ao Menu", "text": "Olá"}
                ]

            # 7. Agradecimento
            elif any(keyword in msg_norm for keyword in ["obrigado", "obrigada", "agradecido", "valeu", "thanks", "obg"]):
                resposta = "De nada! Fico feliz por ajudar. Se tiveres mais alguma dúvida sobre o Laboratório Cultural, estou aqui!"
                sugestoes = [
                    {"label": "🚪 Menu Principal", "text": "Olá"}
                ]

            # 8. Contacto / Enviar mensagem
            elif any(keyword in msg_norm for keyword in ["contacto", "enviar mensagem", "falar", "ajuda", "humano", "mensagem", "suporte", "email", "e-mail"]):
                resposta = (
                    "Se quiseres falar connosco ou enviar uma mensagem de suporte, eu posso recolher a tua mensagem aqui "
                    "e enviá-la para a nossa equipa. Desejas deixar uma mensagem?"
                )
                sugestoes = [
                    {"label": "✉️ Sim, deixar mensagem", "action": "start_message"},
                    {"label": "🚪 Não, voltar ao Menu", "text": "Olá"}
                ]
                
            # 9. Fallback
            else:
                resposta = (
                    f"Não consegui compreender a tua pergunta sobre '{mensagem_original}'. "
                    "Posso ajudar-te com informações sobre o Teatro, a Tuna, a Biblioteca ou a Agenda de Eventos. "
                    "Se preferires, podes enviar uma mensagem diretamente para a nossa equipa de suporte."
                )
                sugestoes = [
                    {"label": "🎭 Clube de Teatro", "text": "Teatro"},
                    {"label": "📚 Biblioteca", "text": "Biblioteca"},
                    {"label": "✉️ Enviar Mensagem", "text": "Enviar Mensagem"},
                    {"label": "🚪 Menu Principal", "text": "Olá"}
                ]
            
        return jsonify({
            "response": resposta,
            "suggestions": sugestoes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/v1/chatbot/submit', methods=['POST'])
def chatbot_submeter_mensagem():
    """Recebe as mensagens submetidas conversacionalmente pelo chatbot e guarda-as na DB."""
    try:
        data = request.get_json() or {}
        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip()
        mensagem = data.get('mensagem', '').strip()
        
        from app.utils.security import sanitize
        try:
            nome = sanitize(nome)
            email = sanitize(email)
            mensagem = sanitize(mensagem)
        except Exception:
            pass
            
        if not nome or not email or not mensagem:
            return jsonify({"success": False, "message": "Por favor, preencha todos os campos."}), 400
            
        if not email.endswith('@ispgaya.pt'):
            return jsonify({"success": False, "message": "Apenas e-mails institucionais (@ispgaya.pt) são aceites."}), 400
            
        from app import get_db
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO mensagens_contacto (nome, email, mensagem) VALUES (?, ?, ?)",
                (nome, email, mensagem)
            )
            db.commit()
            
        return jsonify({"success": True, "message": "Mensagem guardada com sucesso."})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/v1/avaliar-password', methods=['POST'])
def api_avaliar_password():
    """API para avaliar a robustez de uma password."""
    try:
        data = request.get_json() or {}
        password = data.get('password', '')
        
        from app.utils.security import avaliar_password
        classificacao, pontuacao, problemas, contem_padrao_fraco, e_proibida = avaliar_password(password)
        
        return jsonify({
            'classificacao': classificacao,
            'pontuacao': pontuacao,
            'problemas': problemas,
            'contem_padrao_fraco': contem_padrao_fraco,
            'e_proibida': e_proibida
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
