import os
import random
from app import get_db
from flask import Blueprint, render_template, request, abort, Response, jsonify, flash, redirect, url_for, session
from app.utils.security import sanitize
from datetime import datetime, time, timedelta
from app.models.evento import Evento
from app.models.noticia import Noticia
from app.models.livro import Livro, SessaoLeitura, RequisicaoLivro
from app.models.espetaculo import Espetaculo
from app.models.tuna import EspetaculoTuna, MembroTuna
from app.models.categoria import Categoria
from app.models.clube import Clube
from app.models.inscricao_teatro import InscricaoTeatro
from app.utils.email import EmailService
from config import Config

frontoffice_bp = Blueprint('frontoffice', __name__)


@frontoffice_bp.route('/')
def homepage():
    """Página principal do ISPGAYA (homepage estática com links para Lab. Cultural)."""
    return render_template('homepage.html')


@frontoffice_bp.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    import os
    return send_from_directory(os.path.join(frontoffice_bp.root_path, '..', '..', 'static', 'img'),
                               'favicon_ispgaya.png', mimetype='image/png')


@frontoffice_bp.route('/lab-cultural')
def index():
    """Página principal do Laboratório Cultural."""
    try:
        eventos_destaque = Evento.get_destaques(100)
        noticias_destaque = Noticia.get_destaques(100)
        espetaculos_destaque = Espetaculo.get_destaques(100)
    except Exception:
        eventos_destaque = []
        noticias_destaque = []
        espetaculos_destaque = []

    return render_template('lab_cultural/index.html',
                           eventos=eventos_destaque,
                           noticias=noticias_destaque,
                           espetaculos=espetaculos_destaque)


@frontoffice_bp.route('/lab-cultural/enviar-mensagem', methods=['POST'])
def enviar_mensagem():
    """Recebe mensagens do formulário de contacto da homepage."""
    nome = sanitize(request.form.get('nome'))
    email = sanitize(request.form.get('email'))
    mensagem = sanitize(request.form.get('mensagem'))
    
    if not nome or not email or not mensagem:
        flash('Por favor, preencha todos os campos.', 'danger')
        return redirect(url_for('frontoffice.index') + '#contacto')
        
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO mensagens_contacto (nome, email, mensagem) VALUES (?, ?, ?)",
                (nome, email, mensagem)
            )
        db.commit()
        flash('Mensagem enviada com sucesso! Entraremos em contacto brevemente.', 'success')
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        flash('Ocorreu um erro ao enviar a mensagem. Por favor, tente novamente.', 'danger')
        
    return redirect(url_for('frontoffice.index') + '#contacto')



@frontoffice_bp.route('/lab-cultural/clube-leitura')
def clube_leitura():
    """Página do Clube de Leitura."""
    try:
        livros_destaque = Livro.get_destaques(3)
        todos_livros = Livro.get_all()
        calendario = SessaoLeitura.get_calendario(apenas_futuros=True)
    except Exception:
        livros_destaque = []
        todos_livros = []
        calendario = []
    return render_template('lab_cultural/clube_leitura.html',
                           livros_destaque=livros_destaque,
                           todos_livros=todos_livros,
                           calendario=calendario)


@frontoffice_bp.route('/lab-cultural/clube-leitura/biblioteca')
def biblioteca():
    """Listagem completa de todos os livros do clube com filtros."""
    pagina = request.args.get('pagina', 1, type=int)
    filtros = {}
    
    q = request.args.get('q', '').strip()
    genero = request.args.get('genero', '').strip()
    disponibilidade = request.args.get('disponibilidade', '').strip()
    
    if q:
        filtros['q'] = q
    if genero:
        filtros['genero'] = genero
    if disponibilidade in ('disponivel', 'indisponivel'):
        filtros['disponibilidade'] = disponibilidade
    
    por_pagina = 12 # Mais livros por página na biblioteca
    
    try:
        from app.models.livro import Livro
        lista_livros, total = Livro.get_all_paginated(filtros, pagina, por_pagina)
        generos = Livro.get_generos()
    except Exception as e:
        print(f"Erro biblioteca paginada: {e}")
        lista_livros = []
        total = 0
        generos = []
        
    total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
    
    return render_template('lab_cultural/biblioteca.html',
                           livros=lista_livros,
                           generos=generos,
                           pagina=pagina,
                           total_paginas=total_paginas,
                           total=total,
                           filtros_ativos=filtros)


@frontoffice_bp.route('/lab-cultural/clube-teatro')
def clube_teatro():
    """Página do Clube de Teatro."""
    try:
        # Agenda de ensaios e espetáculos - Apenas futuros
        agenda = Espetaculo.get_agenda(apenas_futuros=True)
        
        
        # Registo Fotográfico do Banco de Dados
        registos_db = Espetaculo.get_galeria()
        todos_registos = []
        
        # Para verificar se o ficheiro existe fisicamente
        from flask import current_app
        static_path = current_app.static_folder
        
        if registos_db:
            for r in registos_db:
                # Se o caminho começar com /static/ ou static/, removemos para usar no url_for
                path = r['imagem'].replace('/static/', '').replace('static/', '')
                # Limpar barra inicial se existir após o replace
                if path.startswith('/'): path = path[1:]
                
                # Verificar se o ficheiro existe para evitar 404
                full_path = os.path.join(static_path, path.replace('/', os.sep))
                if os.path.exists(full_path):
                    todos_registos.append(path)
                else:
                    # Se o ficheiro na BD não existe, tentamos encontrar uma da lista que ainda não esteja lá
                    from app import TEATRO_IMAGES
                    for fallback in TEATRO_IMAGES:
                        f_path = 'img/teatro/' + fallback
                        if f_path not in todos_registos:
                            todos_registos.append(f_path)
                            break
            
            # Garantir unicidade final mantendo a ordem (list comprehension com set de controlo)
            seen = set()
            todos_registos = [x for x in todos_registos if not (x in seen or seen.add(x))]
        else:
            # Fallback para fotos da pasta física se a BD estiver vazia
            from app import TEATRO_IMAGES
            todos_registos = ['img/teatro/' + img for img in TEATRO_IMAGES]
        
    except Exception as e:
        print(f"Erro ao carregar página de teatro: {e}")
        agenda = []
        todos_registos = []
    
    # Obter destaques para a página do clube
    espetaculos_destaque = Espetaculo.get_destaques(3)
        
    return render_template('lab_cultural/clube_teatro.html', 
                           agenda=agenda, 
                           espetaculos_destaque=espetaculos_destaque,
                           registos_fotos=todos_registos[:4])


@frontoffice_bp.route('/lab-cultural/clube-teatro/juntar')
def juntar_clube_teatro_form():
    """Página com o formulário para juntar-se ao Clube de Teatro."""
    return render_template('lab_cultural/juntar_clube_teatro.html')


@frontoffice_bp.route('/lab-cultural/clube-teatro/juntar', methods=['POST'])
def juntar_clube_teatro():
    """Processa a inscrição no Clube de Teatro."""
    from app.models.espetaculo import MembroTeatro
    
    nome = request.form.get('nome')
    email = request.form.get('email', '').lower()
    
    if not nome or not email:
        flash('Por favor, preencha todos os campos.', 'error')
        return redirect(url_for('frontoffice.juntar_clube_teatro_form'))
        
    if not email.endswith('@ispgaya.pt'):
        flash('Apenas e-mails institucionais (@ispgaya.pt) são permitidos.', 'error')
        return redirect(url_for('frontoffice.juntar_clube_teatro_form'))
        
    if MembroTeatro.verificar_duplicado(email):
        flash('Já te inscreveste no Clube de Teatro com este e-mail!', 'error')
        return redirect(url_for('frontoffice.juntar_clube_teatro_form'))
        
    dados = {
        'nome': nome,
        'email': email
    }
    
    if MembroTeatro.criar(dados):
        # Enviar e-mail de candidatura recebida (aguarda aprovação)
        try:
            EmailService.enviar_confirmacao_membro_teatro_pendente(email, nome)
        except Exception as e:
            print(f"Erro ao enviar email de candidatura ao teatro: {e}")

        flash('Candidatura submetida!', 'success')
        return render_template('lab_cultural/confirmacao_membro.html',
                               nome=nome,
                               email=email,
                               clube_tipo='teatro')
    else:
        flash('Ocorreu um erro. Tenta novamente mais tarde.', 'error')
        return redirect(url_for('frontoffice.juntar_clube_teatro_form'))

@frontoffice_bp.route('/lab-cultural/clube-teatro/galeria')
def galeria_teatro():
    """Página completa do Registo Fotográfico agrupada por espetáculo."""
    q = request.args.get('q', '').strip()
    lista_grupos = []
    try:
        db = get_db()
        from flask import current_app
        static_path = current_app.static_folder
        from app import TEATRO_IMAGES
        
        with db.cursor() as cursor:
            # 1. Buscar todos os espetáculos que já passaram
            query = """
                SELECT id, titulo, imagem, data_evento
                FROM espetaculos
                WHERE ativo = 1 AND data_evento < date('now', 'localtime')
            """
            params = []
            
            if q:
                query += " AND titulo LIKE ?"
                params.append(f'%{q}%')
                
            query += " ORDER BY data_evento DESC"
            
            cursor.execute(query, params)
            espetaculos_passados = cursor.fetchall()
            
            grupos = []
            
            for esp in espetaculos_passados:
                # 2. Buscar fotos na galeria para este espetáculo
                cursor.execute("""
                    SELECT * FROM galeria_teatro 
                    WHERE espetaculo_id = ? AND ativo = 1
                    ORDER BY ordem ASC, criado_em DESC
                """, (esp['id'],))
                fotos_galeria = cursor.fetchall()
                
                fotos_processadas = []
                
                # Se houver fotos na galeria, processamos
                if fotos_galeria:
                    for f in fotos_galeria:
                        img_raw = f['imagem'] or ''
                        path = img_raw.replace('/static/', '').replace('static/', '')
                        if path.startswith('/'): path = path[1:]
                        
                        full_path = os.path.join(static_path, path.replace('/', os.sep))
                        if os.path.exists(full_path) and path:
                            f['path'] = path
                        else:
                            f['path'] = 'img/teatro/' + TEATRO_IMAGES[f['id'] % len(TEATRO_IMAGES)]
                        fotos_processadas.append(f)
                else:
                    # Se não houver fotos na galeria, usamos a imagem do espetáculo como fallback
                    img_esp = esp['imagem'] or ''
                    path = img_esp.replace('/static/', '').replace('static/', '')
                    if path.startswith('/'): path = path[1:]
                    
                    # Criar entrada virtual
                    fotos_processadas.append({
                        'id': 0,
                        'titulo': esp['titulo'],
                        'path': path if path else 'img/teatro/teatro1.jpg',
                        'criado_em': esp['data_evento']
                    })
                
                grupos.append({
                    'nome': esp['titulo'],
                    'data': esp['data_evento'],
                    'fotos': fotos_processadas
                })
            
            lista_grupos = grupos

        # Se após processar a DB ainda não temos nada, usamos o fallback total
        if not lista_grupos:
            fotos_fallback = []
            for i, img in enumerate(TEATRO_IMAGES):
                fotos_fallback.append({
                    'id': i,
                    'titulo': f'Registo {i+1}',
                    'legenda': 'Momento capturado em palco pelo Clube de Teatro.',
                    'path': 'img/teatro/' + img,
                    'criado_em': None
                })
            lista_grupos = [{'nome': 'Galeria Geral', 'fotos': fotos_fallback}]
                
    except Exception as e:
        print(f"Erro Crítico Galeria: {e}")
        # Fallback de segurança em caso de erro de DB
        lista_grupos = [{'nome': 'Galeria', 'fotos': []}]
        
    return render_template('lab_cultural/galeria_teatro.html', grupos=lista_grupos, clube_tipo='teatro')


@frontoffice_bp.route('/lab-cultural/clube-teatro/agenda-completa')
def espetaculos_lista():
    """Listagem completa da agenda com filtros."""
    pagina = request.args.get('pagina', 1, type=int)
    filtros = {}
    
    tipo = request.args.get('tipo', '').strip()
    entrada = request.args.get('entrada', '').strip()
    q = request.args.get('q', '').strip()
    data_de = request.args.get('data_de', '').strip()
    destaque = request.args.get('destaque', '').strip()
    
    if tipo in ('espetaculo', 'ensaio', 'workshop'):
        filtros['tipo'] = tipo
    if entrada in ('gratuita', 'pago', 'convite'):
        filtros['entrada'] = entrada
    if q:
        filtros['q'] = q
    if data_de:
        filtros['data_de'] = data_de
    if destaque == '1':
        filtros['destaque'] = True
        
    por_pagina = 6 # Reduzido de Config.ITEMS_PER_PAGE (9) para 6 para mostrar a paginação (temos 7 itens)
    filtros['apenas_publicados'] = True
    filtros['apenas_futuros'] = True
    
    try:
        lista_espetaculos, total = Espetaculo.get_all_paginated(filtros, pagina, por_pagina)
    except Exception as e:
        print(f"Erro agenda paginada: {e}")
        lista_espetaculos = []
        total = 0
        
    total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
    
    return render_template('lab_cultural/espetaculos_lista.html',
                           agenda=lista_espetaculos,
                           pagina=pagina,
                           total_paginas=total_paginas,
                           total=total,
                           filtros_ativos=filtros)


# ─── TUNA ACADÉMICA ─────────────────────────────────────────────────
@frontoffice_bp.route('/lab-cultural/tuna')
def clube_tuna():
    """Página informativa da Tuna Académica (Atuna Bira Copos)."""
    return render_template('lab_cultural/clube_tuna.html')


@frontoffice_bp.route('/lab-cultural/tuna/juntar')
def juntar_tuna_form():
    """Página com o formulário para juntar-se à Tuna Académica."""
    return render_template('lab_cultural/juntar_clube_tuna.html')


@frontoffice_bp.route('/lab-cultural/tuna/juntar', methods=['POST'])
def juntar_tuna():
    """Processa a inscrição na Tuna Académica."""
    nome = request.form.get('nome')
    email = request.form.get('email', '').lower()
    
    if not nome or not email:
        flash('Por favor, preencha todos os campos.', 'error')
        return redirect(url_for('frontoffice.juntar_tuna_form'))
        
    if not email.endswith('@ispgaya.pt'):
        flash('Apenas e-mails institucionais (@ispgaya.pt) são permitidos.', 'error')
        return redirect(url_for('frontoffice.juntar_tuna_form'))
        
    if MembroTuna.verificar_duplicado(email):
        flash('Já te inscreveste na Tuna Académica com este e-mail!', 'error')
        return redirect(url_for('frontoffice.juntar_tuna_form'))
        
    dados = {
        'nome': nome,
        'email': email
    }
    
    if MembroTuna.criar(dados):
        try:
            EmailService.enviar_confirmacao_membro_tuna_pendente(email, nome)
        except Exception as e:
            print(f"Erro ao enviar email de candidatura à tuna: {e}")

        flash('Candidatura submetida!', 'success')
        return render_template('lab_cultural/confirmacao_membro.html',
                               nome=nome,
                               email=email,
                               clube_tipo='tuna')
    else:
        flash('Ocorreu um erro. Tenta novamente mais tarde.', 'error')
        return redirect(url_for('frontoffice.juntar_tuna_form'))


@frontoffice_bp.route('/lab-cultural/tuna/galeria')
def galeria_tuna():
    """Página completa do Registo Fotográfico da Tuna."""
    q = request.args.get('q', '').strip()
    lista_grupos = []
    try:
        db = get_db()
        from flask import current_app
        static_path = current_app.static_folder
        from app import TEATRO_IMAGES
        
        with db.cursor() as cursor:
            query = """
                SELECT id, titulo, imagem, data_evento
                FROM espetaculos_tuna
                WHERE ativo = 1
            """
            params = []
            
            if q:
                query += " AND titulo LIKE ?"
                params.append(f'%{q}%')
                
            query += " ORDER BY data_evento DESC"
            
            cursor.execute(query, params)
            espetaculos_passados = cursor.fetchall()
            
            grupos = []
            
            for esp in espetaculos_passados:
                cursor.execute("""
                    SELECT * FROM galeria_tuna 
                    WHERE espetaculo_id = ? AND ativo = 1
                    ORDER BY ordem ASC, criado_em DESC
                """, (esp['id'],))
                fotos_galeria = cursor.fetchall()
                
                fotos_processadas = []
                
                if fotos_galeria:
                    for f in fotos_galeria:
                        img_raw = f['imagem'] or ''
                        path = img_raw.replace('/static/', '').replace('static/', '')
                        if path.startswith('/'): path = path[1:]
                        
                        full_path = os.path.join(static_path, path.replace('/', os.sep))
                        if os.path.exists(full_path) and path:
                            f['path'] = path
                        else:
                            f['path'] = 'img/teatro/' + TEATRO_IMAGES[f['id'] % len(TEATRO_IMAGES)]
                        fotos_processadas.append(f)
                else:
                    img_esp = esp['imagem'] or ''
                    path = img_esp.replace('/static/', '').replace('static/', '')
                    if path.startswith('/'): path = path[1:]
                    
                    fotos_processadas.append({
                        'id': 0,
                        'titulo': esp['titulo'],
                        'path': path if path else 'img/teatro/teatro1.jpg',
                        'criado_em': esp['data_evento']
                    })
                
                grupos.append({
                    'nome': esp['titulo'],
                    'data': esp['data_evento'],
                    'fotos': fotos_processadas
                })
            
            lista_grupos = grupos

        if not lista_grupos:
            fotos_fallback = []
            for i, img in enumerate(TEATRO_IMAGES):
                fotos_fallback.append({
                    'id': i,
                    'titulo': f'Registo {i+1}',
                    'legenda': 'Momento capturado pela Tuna Académica.',
                    'path': 'img/teatro/' + img,
                    'criado_em': None
                })
            lista_grupos = [{'nome': 'Galeria Geral', 'fotos': fotos_fallback}]
                
    except Exception as e:
        print(f"Erro Crítico Galeria Tuna: {e}")
        lista_grupos = [{'nome': 'Galeria', 'fotos': []}]
        
    return render_template('lab_cultural/galeria_teatro.html', grupos=lista_grupos, clube_tipo='tuna')


@frontoffice_bp.route('/lab-cultural/tuna/<int:esp_id>')
def tuna_espetaculo_detalhe(esp_id):
    """Detalhe de uma atuação da Tuna."""
    espetaculo = EspetaculoTuna.get_by_id(esp_id)
    if not espetaculo:
        abort(404)
    
    fotos = EspetaculoTuna.get_fotos_by_espetaculo(esp_id)
    
    return render_template('lab_cultural/espetaculo_detalhe.html',
                           espetaculo=espetaculo,
                           fotos=fotos)


@frontoffice_bp.route('/lab-cultural/eventos')
def eventos():
    """Listagem de eventos culturais com filtros."""
    pagina = request.args.get('pagina', 1, type=int)
    filtros = {}

    cidade = request.args.get('cidade', '').strip()
    categoria_id = request.args.get('categoria_id', '').strip()
    tipo = request.args.get('tipo', '').strip()
    
    q = request.args.get('q', '').strip()
    disponibilidade_filtro = request.args.get('disponibilidade', '').strip()
    data_de = request.args.get('data_de', '').strip()
    data_ate = request.args.get('data_ate', '').strip()

    if q:
        filtros['q'] = q
    if cidade:
        filtros['cidade'] = cidade
    if categoria_id:
        filtros['categoria_id'] = int(categoria_id)
    if tipo in ('interno', 'externo'):
        filtros['tipo'] = tipo
    if disponibilidade_filtro == 'disponivel':
        filtros['disponibilidade'] = disponibilidade_filtro
    if data_de:
        filtros['data_de'] = data_de
        filtros['data_ate'] = data_de # Filtra apenas o dia selecionado
    if data_ate:
        filtros['data_ate'] = data_ate

    por_pagina = Config.ITEMS_PER_PAGE

    try:
        lista_eventos, total = Evento.get_all(filtros, pagina, por_pagina, apenas_futuros=True)
        categorias = Categoria.get_all()
        cidades = Evento.get_cidades()
    except Exception:
        lista_eventos = []
        total = 0
        categorias = []
        cidades = []

    total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0

    # Calcular disponibilidade por evento (apenas os que têm limite de bilhetes)
    disponibilidade = {}
    for ev in lista_eventos:
        if ev.get('limite_bilhetes'):
            inscritos = Evento.contar_inscritos(ev['id'])
            disponibilidade[ev['id']] = max(0, ev['limite_bilhetes'] - inscritos)

    return render_template('lab_cultural/eventos.html',
                           eventos=lista_eventos,
                           categorias=categorias,
                           cidades=cidades,
                           pagina=pagina,
                           total_paginas=total_paginas,
                           total=total,
                           filtros_ativos=filtros,
                           disponibilidade=disponibilidade)


@frontoffice_bp.route('/lab-cultural/eventos/<int:evento_id>')
def evento_detalhe(evento_id: int):
    """Página de detalhe de um evento."""
    from datetime import date
    try:
        evento = Evento.get_by_id(evento_id)
    except Exception:
        evento = None
    if not evento:
        abort(404)
        
    # Se o evento ainda não foi publicado, retorna 404
    if evento.get('data_publicacao') and evento['data_publicacao'] > datetime.now():
        abort(404)
    try:
        outros, _ = Evento.get_all(pagina=1, por_pagina=4, apenas_futuros=True)
        outros = [e for e in outros if e['id'] != evento_id][:3]
    except Exception:
        outros = []
    # Calcular disponibilidade de bilhetes
    bilhetes_disponiveis = None
    if evento.get('limite_bilhetes'):
        inscritos = Evento.contar_inscritos(evento_id)
        bilhetes_disponiveis = max(0, evento['limite_bilhetes'] - inscritos)

    # Fotos da Galeria
    fotos = Evento.get_galeria(evento_id)

    return render_template('lab_cultural/evento_detalhe.html',
                           evento=evento,
                           outros_eventos=outros,
                           bilhetes_disponiveis=bilhetes_disponiveis,
                           hoje=date.today(),
                           fotos=fotos)


@frontoffice_bp.route('/lab-cultural/eventos/<int:evento_id>/inscrever')
def inscrever_evento_form(evento_id: int):
    """Página com o formulário de inscrição para um evento cultural."""
    try:
        evento = Evento.get_by_id(evento_id)
    except Exception:
        evento = None
    if not evento:
        abort(404)
        
    # Calcular disponibilidade de bilhetes
    bilhetes_disponiveis = None
    if evento.get('limite_bilhetes'):
        inscritos = Evento.contar_inscritos(evento_id)
        bilhetes_disponiveis = max(0, evento['limite_bilhetes'] - inscritos)
        
    return render_template('lab_cultural/inscricao_evento.html', 
                           evento=evento, 
                           bilhetes_disponiveis=bilhetes_disponiveis)


@frontoffice_bp.route('/lab-cultural/eventos/<int:evento_id>/processar-inscricao', methods=['POST'])
def inscrever_evento(evento_id: int):
    """Processa a inscrição/compra de bilhete para um evento cultural."""
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip().lower()

    if not nome or not email:
        flash('Por favor, preencha o nome e o e-mail.', 'error')
        return redirect(url_for('frontoffice.inscrever_evento_form', evento_id=evento_id))

    # Validar domínio @ispgaya.pt
    if not email.endswith('@ispgaya.pt'):
        flash('Apenas e-mails institucionais @ispgaya.pt são permitidos.', 'error')
        return redirect(url_for('frontoffice.inscrever_evento_form', evento_id=evento_id))

    # Garantir que só eventos internos ISPGAYA permitem inscrição
    evento_check = Evento.get_by_id(evento_id)
    if not evento_check or evento_check.get('tipo') != 'interno':
        flash('Inscrições apenas disponíveis para eventos internos ISPGAYA.', 'error')
        return redirect(url_for('frontoffice.evento_detalhe', evento_id=evento_id))

    resultado = Evento.inscrever(evento_id, nome, email)

    if not resultado['ok']:
        flash(resultado['erro'], 'error')
        return redirect(url_for('frontoffice.inscrever_evento_form', evento_id=evento_id))

    # Enviar e-mail de confirmação com bilhete PDF
    evento = Evento.get_by_id(evento_id)
    if evento:
        EmailService.enviar_bilhete(email, nome, evento, resultado['codigo'])

    flash('Inscrição confirmada! O bilhete foi enviado para o seu e-mail.', 'success')
    return redirect(url_for('frontoffice.evento_detalhe', evento_id=evento_id))


@frontoffice_bp.route('/lab-cultural/clube-teatro/espetaculo/<int:esp_id>')
def espetaculo_detalhe(esp_id: int):
    """Página de detalhe de um espetáculo/ensaio."""
    from datetime import date
    try:
        espetaculo = Espetaculo.get_by_id(esp_id)
    except Exception:
        espetaculo = None
        
    if not espetaculo:
        abort(404)
        
    try:
        agenda = Espetaculo.get_agenda()
        relacionados = [e for e in agenda if e['id'] != esp_id][:3]
    except Exception:
        relacionados = []
        
    fotos = Espetaculo.get_fotos_by_espetaculo(esp_id)
    
    return render_template('lab_cultural/espetaculo_detalhe.html',
                           espetaculo=espetaculo,
                           relacionados=relacionados,
                           fotos=fotos,
                           hoje=date.today())


@frontoffice_bp.route('/lab-cultural/clube-teatro/espetaculo/<int:esp_id>/inscrever')
def inscrever_teatro_form(esp_id: int):
    """Página com o formulário de inscrição para um espetáculo."""
    try:
        espetaculo = Espetaculo.get_by_id(esp_id)
    except Exception:
        espetaculo = None
        
    if not espetaculo:
        abort(404)
        
    return render_template('lab_cultural/inscricao_espetaculo.html', espetaculo=espetaculo)


@frontoffice_bp.route('/lab-cultural/clube-teatro/inscricao/<int:esp_id>', methods=['POST'])
def inscrever_teatro(esp_id: int):
    """Processa a inscrição e gera o bilhete."""
    espetaculo = Espetaculo.get_by_id(esp_id)
    if not espetaculo:
        abort(404)
        
    nome = request.form.get('nome')
    email = request.form.get('email', '').lower()
    
    # Validação rigorosa de e-mail institucional
    if not email.endswith('@ispgaya.pt'):
        flash('Erro: Apenas e-mails @ispgaya.pt são permitidos.', 'error')
        return redirect(url_for('frontoffice.inscrever_teatro_form', esp_id=esp_id))
        
    # Verificar se já está inscrito
    if InscricaoTeatro.verificar_duplicado(esp_id, email):
        flash('Este e-mail já possui uma reserva para este espetáculo. Apenas 1 reserva por e-mail é permitida.', 'error')
        return redirect(url_for('frontoffice.inscrever_teatro_form', esp_id=esp_id))

    # Verificar limite de lotação geral do espetáculo
    limite_filas = espetaculo.get('limite_filas', 8)
    lotacao_total = limite_filas * 12
    inscritos = Espetaculo.contar_inscritos(esp_id)
    if inscritos >= lotacao_total:
        flash('Erro: Este espetáculo já atingiu a lotação máxima.', 'error')
        return redirect(url_for('frontoffice.espetaculo_detalhe', esp_id=esp_id))

    lugares = "Geral"
    dados = {
        'espetaculo_id': esp_id,
        'nome': nome,
        'email': email,
        'lugares': lugares
    }
    
    codigo = InscricaoTeatro.criar(dados)
    
    if not codigo:
        flash('Erro ao processar inscrição. Tente novamente.', 'error')
        return redirect(url_for('frontoffice.inscrever_teatro_form', esp_id=esp_id))
        
    # Enviar e-mail de confirmação com bilhete PDF em anexo
    # Passamos os lugares_espetaculo no espetaculo ou de outra forma para gerar no bilhete, 
    # mas por simplicidade podemos passar pelo "espetaculo" objecto dinamico para o EmailService
    espetaculo_ticket = dict(espetaculo)
    espetaculo_ticket['lugares_selecionados'] = lugares
    EmailService.enviar_bilhete(email, nome, espetaculo_ticket, codigo)
        
    # Renderizar página de confirmação (em vez do bilhete direto)
    return render_template('lab_cultural/confirmacao_inscricao.html',
                           espetaculo=espetaculo,
                           nome=nome,
                           email=email,
                           codigo=codigo,
                           lugares=lugares)


@frontoffice_bp.route('/lab-cultural/clube-leitura/livro/<int:livro_id>')
def livro_detalhe(livro_id: int):
    """Página de detalhe de um livro."""
    from app.models.livro import Livro
    try:
        livro = Livro.get_by_id(livro_id)
    except Exception:
        livro = None
    if not livro:
        abort(404)

    try:
        relacionados = Livro.get_destaques(limite=3)
        relacionados = [l for l in relacionados if l['id'] != livro_id][:3]
    except Exception:
        relacionados = []

    requisicao_ativa = None
    if str(livro.get('esta_disponivel')) == '0':
        requisicao_ativa = RequisicaoLivro.get_ativa_by_livro(livro_id)

    return render_template('lab_cultural/livro_detalhe.html',
                           livro=livro,
                           relacionados=relacionados,
                           requisicao_ativa=requisicao_ativa)


@frontoffice_bp.route('/lab-cultural/clube-leitura/livro/<int:livro_id>/requisitar')
def requisitar_livro_form(livro_id: int):
    """Página com o formulário de requisição para um livro."""
    try:
        livro = Livro.get_by_id(livro_id)
    except Exception:
        livro = None
        
    if not livro:
        abort(404)
        
    return render_template('lab_cultural/requisicao_livro.html', livro=livro)


@frontoffice_bp.route('/lab-cultural/clube-leitura/livro/<int:livro_id>/requisitar', methods=['POST'])
def requisitar_livro(livro_id: int):
    """Processa a requisição de um livro."""
    livro = Livro.get_by_id(livro_id)
    if not livro:
        abort(404)
        
    nome = request.form.get('nome')
    email = request.form.get('email', '').lower()
    
    if not nome or not email:
        flash('Por favor, preencha todos os campos.', 'error')
        return redirect(url_for('frontoffice.requisitar_livro_form', livro_id=livro_id))

    # Validação de e-mail institucional
    if not email.endswith('@ispgaya.pt'):
        flash('Erro: Apenas e-mails @ispgaya.pt são permitidos.', 'error')
        return redirect(url_for('frontoffice.requisitar_livro_form', livro_id=livro_id))
        
    # Verificar se já tem uma requisição pendente para este livro
    if RequisicaoLivro.verificar_duplicado(livro_id, email):
        flash('Já tens uma requisição pendente para este livro.', 'warning')
        return redirect(url_for('frontoffice.livro_detalhe', livro_id=livro_id))

    dados = {
        'livro_id': livro_id,
        'nome': nome,
        'email': email
    }
    
    codigo = RequisicaoLivro.criar(dados)
    
    if not codigo:
        flash('Erro ao processar a requisição. Tente novamente.', 'error')
        return redirect(url_for('frontoffice.requisitar_livro_form', livro_id=livro_id))
        
    # Enviar e-mail de "pedido recebido" (sem código - código só após aprovação do admin)
    EmailService.enviar_requisicao_pendente(email, nome, livro['titulo'])
        
    return render_template('lab_cultural/confirmacao_requisicao.html',
                           livro=livro,
                           nome=nome,
                           email=email,
                           codigo=None)


@frontoffice_bp.route('/lab-cultural/clube-leitura/sessao/<int:sessao_id>/inscrever')
def inscrever_sessao_form(sessao_id: int):
    """Página com o formulário de inscrição para uma sessão de leitura."""
    from app.models.livro import SessaoLeitura
    sessao = SessaoLeitura.get_by_id(sessao_id)
    if not sessao:
        abort(404)
        
    return render_template('lab_cultural/inscricao_sessao.html', sessao=sessao)


@frontoffice_bp.route('/lab-cultural/clube-leitura/sessao/<int:sessao_id>/inscrever', methods=['POST'])
def inscrever_sessao_leitura(sessao_id: int):
    """Processa a inscrição numa sessão de leitura."""
    from app.models.livro import InscricaoLeitura, SessaoLeitura
    sessao = SessaoLeitura.get_by_id(sessao_id)
    if not sessao:
        abort(404)
        
    nome = request.form.get('nome')
    email = request.form.get('email', '').lower()
    
    if not nome or not email:
        flash('Por favor, preencha todos os campos.', 'error')
        return redirect(url_for('frontoffice.inscrever_sessao_form', sessao_id=sessao_id))
        
    if not email.endswith('@ispgaya.pt'):
        flash('Apenas e-mails @ispgaya.pt são válidos.', 'error')
        return redirect(url_for('frontoffice.inscrever_sessao_form', sessao_id=sessao_id))
        
    if InscricaoLeitura.verificar_duplicado(sessao_id, email):
        flash('Já se inscreveu nesta sessão com este e-mail.', 'error')
        return redirect(url_for('frontoffice.inscrever_sessao_form', sessao_id=sessao_id))
        
    dados = {
        'sessao_id': sessao_id,
        'nome': nome,
        'email': email
    }
    
    if InscricaoLeitura.criar(dados):
        from app.utils.email import EmailService
        data_hora = f"{sessao.get('data_sessao').strftime('%d/%m/%Y') if sessao.get('data_sessao') else 'A anunciar'} às {sessao.get('hora', '18:00')}"
        local = sessao.get('local') or 'ISPGAYA'
        EmailService.enviar_confirmacao_sessao_leitura(email, nome, sessao.get('tema'), data_hora, local)
        flash('Inscrição confirmada!', 'success')
        return render_template('lab_cultural/confirmacao_sessao.html',
                               sessao=sessao,
                               nome=nome,
                               email=email)
    else:
        flash('Erro ao processar inscrição. Tenta novamente.', 'error')
        return redirect(url_for('frontoffice.inscrever_sessao_form', sessao_id=sessao_id))

@frontoffice_bp.route('/lab-cultural/clube-leitura/juntar')
def juntar_clube_leitura_form():
    """Página com o formulário para juntar-se ao Clube de Leitura."""
    return render_template('lab_cultural/juntar_clube_leitura.html')

@frontoffice_bp.route('/lab-cultural/clube-leitura/juntar', methods=['POST'])
def juntar_clube_leitura():
    """Processa a inscrição no Clube de Leitura."""
    from app.models.livro import MembroLeitura
    
    nome = request.form.get('nome')
    email = request.form.get('email', '').lower()
    
    if not nome or not email:
        flash('Por favor, preencha todos os campos.', 'error')
        return redirect(url_for('frontoffice.juntar_clube_leitura_form'))
        
    if not email.endswith('@ispgaya.pt'):
        flash('Apenas e-mails institucionais (@ispgaya.pt) são permitidos.', 'error')
        return redirect(url_for('frontoffice.juntar_clube_leitura_form'))
        
    if MembroLeitura.verificar_duplicado(email):
        flash('Já te inscreveste no Clube de Leitura com este e-mail!', 'error')
        return redirect(url_for('frontoffice.juntar_clube_leitura_form'))
        
    dados = {
        'nome': nome,
        'email': email
    }
    
    if MembroLeitura.criar(dados):
        flash('Candidatura submetida!', 'success')
        return render_template('lab_cultural/confirmacao_membro.html',
                               nome=nome,
                               email=email)
    else:
        flash('Ocorreu um erro. Tenta novamente mais tarde.', 'error')
        return redirect(url_for('frontoffice.juntar_clube_leitura_form'))


@frontoffice_bp.route('/lab-cultural/clube/<slug>')
def clube_dinamico(slug):
    """Página pública de um clube dinâmico."""
    clube = Clube.get_by_slug(slug)
    if not clube:
        abort(404)
    return render_template('lab_cultural/clube_dinamico.html', clube=clube)


@frontoffice_bp.route('/lab-cultural/export-calendar/<tipo>/<int:item_id>')
def export_calendar(tipo, item_id):
    """Gera um ficheiro .ics para download."""
    if tipo == 'evento':
        item = Evento.get_by_id(item_id)
    elif tipo == 'espetaculo':
        item = Espetaculo.get_by_id(item_id)
    else:
        abort(404)
        
    if not item:
        abort(404)
        
    # Preparar datas
    dt_val = item['data_evento']
    hora_val = item.get('hora')
    
    if hora_val:
        try:
            # Garante que hora_val é string no formato HH:MM
            h_str = str(hora_val).split(':')
            dt_start = datetime.combine(dt_val, time(int(h_str[0]), int(h_str[1])))
        except Exception:
            dt_start = datetime.combine(dt_val, time(0, 0))
    else:
        dt_start = datetime.combine(dt_val, time(0, 0))
        
    dt_end = dt_start + timedelta(hours=2) # Duração padrão de 2h
    
    # Formato ICS: YYYYMMDDTHHMMSS
    # Para evitar problemas de fuso horário, usamos o formato 'floating time' (sem Z)
    # que assume o fuso horário do dispositivo do utilizador.
    f_start = dt_start.strftime('%Y%m%dT%H%M%S')
    f_end = dt_end.strftime('%Y%m%dT%H%M%S')
    
    summary = item['titulo'].replace(',', '\\,')
    location = (item.get('local') or item.get('cidade') or '').replace(',', '\\,')
    description = (item.get('descricao') or '').replace('\n', '\\n')[:200]
    
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ISPGAYA//Lab Cultural//PT",
        "BEGIN:VEVENT",
        f"SUMMARY:{summary}",
        f"DTSTART:{f_start}",
        f"DTEND:{f_end}",
        f"LOCATION:{location}",
        f"DESCRIPTION:{description}",
        "END:VEVENT",
        "END:VCALENDAR"
    ]
    
    return Response(
        "\r\n".join(ics_lines),
        mimetype="text/calendar",
        headers={"Content-disposition": f"attachment; filename=evento_{item_id}.ics"}
    )


@frontoffice_bp.app_errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('404.html'), 404

@frontoffice_bp.route('/lab-cultural/noticias')
def noticias():
    from app.models.categoria import Categoria
    from app.models.noticia import Noticia
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 9
    
    filtros_ativos = {}
    q = request.args.get('q', '').strip()
    categoria_id = request.args.get('categoria_id', '').strip()
    data_de = request.args.get('data_de', '').strip()
    data_ate = request.args.get('data_ate', '').strip()
    
    if q: filtros_ativos['q'] = q
    if categoria_id and categoria_id.isdigit(): filtros_ativos['categoria_id'] = int(categoria_id)
    if data_de: filtros_ativos['data_de'] = data_de
    if data_ate: filtros_ativos['data_ate'] = data_ate
    
    try:
        lista_noticias, total = Noticia.get_all(filtros_ativos, pagina, por_pagina)
        categorias = Categoria.get_all()
    except Exception:
        lista_noticias = []
        total = 0
        categorias = []
        
    total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
    
    return render_template('lab_cultural/noticias.html', 
                           categorias=categorias,
                           noticias=lista_noticias,
                           filtros_ativos=filtros_ativos,
                           pagina=pagina,
                           total_paginas=total_paginas)

@frontoffice_bp.route('/lab-cultural/noticias/<int:noticia_id>')
def noticia_detalhe(noticia_id: int):
    from app.models.noticia import Noticia
    noticia = Noticia.get_by_id(noticia_id)
    if not noticia:
        return render_template('erros/404.html'), 404
    return render_template('lab_cultural/noticia_detalhe.html', noticia=noticia)
