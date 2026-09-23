from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response, jsonify
from app import get_db
from app.controllers.auth import login_required, role_required
from app.models.evento import Evento
from app.models.noticia import Noticia
from app.models.livro import Livro, SessaoLeitura
from app.models.espetaculo import Espetaculo
from app.models.categoria import Categoria
from app.models.utilizador import Utilizador
from app.models.clube import Clube
from app.utils.security import validar_campos
from config import Config
import os
import uuid
import csv
import io
import base64
from app.utils.portugal import MUNICIPIOS_PORTUGAL
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup

backoffice_bp = Blueprint('backoffice', __name__)

@backoffice_bp.context_processor
def inject_server_time():
    from datetime import datetime
    return {'agora_server': datetime.now()}


def processar_upload(file, pasta):
    """Auxiliar para guardar imagem e retornar o caminho relativo."""
    if not file or file.filename == '':
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        return None
        
    filename = f"{uuid.uuid4().hex}.{ext}"
    caminho_dir = os.path.join(Config.UPLOAD_FOLDER, pasta)
    
    if not os.path.exists(caminho_dir):
        os.makedirs(caminho_dir)
        
    file.save(os.path.join(caminho_dir, filename))
    return f"uploads/{pasta}/{filename}"


# ─── DASHBOARD ────────────────────────────────────────────────
@backoffice_bp.route('/')
@login_required
def dashboard():
    role = session.get('admin_role', 'admin')
    stats = {}
    eventos_recentes = []

    if role in ('admin', 'conteudo'):
        eventos, total_eventos = Evento.get_all(pagina=1, por_pagina=1000)
        noticias, total_noticias = Noticia.get_all(pagina=1, por_pagina=1000)
        categorias = Categoria.get_all()
        stats['eventos'] = total_eventos
        stats['noticias'] = total_noticias
        stats['categorias'] = len(categorias)
        eventos_recentes, _ = Evento.get_all(pagina=1, por_pagina=5)

    if role in ('admin', 'leitura'):
        livros = Livro.get_all()
        stats['livros'] = len(livros)

    if role in ('admin', 'teatro'):
        agenda = Espetaculo.get_agenda()
        stats['espetaculos'] = len(agenda)

    if role == 'admin':
        utilizadores = Utilizador.get_all()
        clubes = Clube.get_all()
        stats['utilizadores'] = len(utilizadores)
        stats['clubes'] = len(clubes)

    return render_template('backoffice/dashboard.html',
                           stats=stats,
                           eventos_recentes=eventos_recentes)


# ─── MENSAGENS DE CONTACTO ────────────────────────────────────
@backoffice_bp.route('/mensagens')
@role_required('admin')
def listar_mensagens():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("UPDATE mensagens_contacto SET lida = 1 WHERE lida = 0")
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao marcar mensagens como lidas: {e}")
        
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM mensagens_contacto ORDER BY criado_em DESC")
        mensagens = cursor.fetchall()
        
    return render_template('backoffice/mensagens/listar.html', mensagens=mensagens)


@backoffice_bp.route('/mensagens/<int:msg_id>/eliminar', methods=['POST'])
@role_required('admin')
def eliminar_mensagem(msg_id):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM mensagens_contacto WHERE id = ?", (msg_id,))
        db.commit()
        flash('Mensagem eliminada com sucesso.', 'success')
    except Exception:
        db.rollback()
        flash('Erro ao eliminar a mensagem.', 'error')
    return redirect(url_for('backoffice.listar_mensagens'))


# ─── UTILIZADORES (admin only) ───────────────────────────────
@backoffice_bp.route('/utilizadores')
@role_required('admin')
def listar_utilizadores():
    utilizadores = Utilizador.get_all()
    return render_template('backoffice/utilizadores/listar.html', utilizadores=utilizadores)


@backoffice_bp.route('/utilizadores/novo', methods=['GET', 'POST'])
@role_required('admin')
def criar_utilizador():
    clubes = Clube.get_all_admin()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['nome', 'username', 'email', 'password', 'role'])
        password = dados.get('password', '')
        if password:
            from app.utils.security import avaliar_password
            classificacao, pontuacao, problemas, contem_padrao_fraco, e_proibida = avaliar_password(password)
            if classificacao == 'Fraca':
                erros.extend(problemas)
        if erros:
            return render_template('backoffice/utilizadores/form.html',
                                   clubes=clubes, erros=erros, dados=dados, modo='criar')
        if Utilizador.criar(dados):
            flash('Utilizador criado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_utilizadores'))
        flash('Erro ao criar utilizador (username ou email já existem?).', 'error')
    return render_template('backoffice/utilizadores/form.html',
                           clubes=clubes, erros=[], dados={}, modo='criar')


@backoffice_bp.route('/utilizadores/<int:user_id>/editar', methods=['GET', 'POST'])
@role_required('admin')
def editar_utilizador(user_id: int):
    utilizador = Utilizador.get_by_id(user_id)
    if not utilizador:
        flash('Utilizador não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_utilizadores'))
    clubes = Clube.get_all_admin()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['nome', 'username', 'email', 'role'])
        password = dados.get('password', '').strip()
        if password:
            from app.utils.security import avaliar_password
            classificacao, pontuacao, problemas, contem_padrao_fraco, e_proibida = avaliar_password(password)
            if classificacao == 'Fraca':
                erros.extend(problemas)
            else:
                # Prevenir reutilização de passwords
                db = get_db()
                with db.cursor() as cursor:
                    cursor.execute("SELECT password FROM utilizadores WHERE id = ?", (user_id,))
                    res = cursor.fetchone()
                    current_hash = res['password'] if res else None
                
                if current_hash and Utilizador.verificar_password(password, current_hash):
                    erros.append("A nova password não pode ser igual à password atual.")
                else:
                    # Comparar com histórico (últimas 3)
                    historico = Utilizador.obter_historico_passwords(user_id)
                    for h_hash in historico:
                        if Utilizador.verificar_password(password, h_hash):
                            erros.append("Não pode reutilizar uma password recentemente utilizada (histórico de passwords).")
                            break
        if erros:
            return render_template('backoffice/utilizadores/form.html',
                                   clubes=clubes, erros=erros, dados=dados, modo='editar', utilizador=utilizador)
        if Utilizador.editar(user_id, dados):
            flash('Utilizador atualizado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_utilizadores'))
        flash('Erro ao atualizar utilizador.', 'error')
    return render_template('backoffice/utilizadores/form.html',
                           clubes=clubes, erros=[], dados=utilizador, modo='editar', utilizador=utilizador)


@backoffice_bp.route('/utilizadores/<int:user_id>/eliminar', methods=['POST'])
@role_required('admin')
def eliminar_utilizador(user_id: int):
    # Não permitir eliminar o próprio utilizador
    if user_id == session.get('admin_id'):
        flash('Não pode eliminar a sua própria conta.', 'error')
    elif Utilizador.eliminar(user_id):
        flash('Utilizador desativado.', 'success')
    else:
        flash('Erro ao eliminar utilizador.', 'error')
    return redirect(url_for('backoffice.listar_utilizadores'))


# ─── CLUBES (admin only) ─────────────────────────────────────
@backoffice_bp.route('/clubes')
@role_required('admin')
def listar_clubes():
    clubes = Clube.get_all_admin()
    return render_template('backoffice/clubes/listar.html', clubes=clubes)


@backoffice_bp.route('/clubes/novo', methods=['GET', 'POST'])
@role_required('admin')
def criar_clube():
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['nome'])
        if erros:
            return render_template('backoffice/clubes/form.html',
                                   erros=erros, dados=dados, modo='criar')
        if Clube.criar(dados):
            flash('Clube criado com sucesso! A página pública já está disponível.', 'success')
            return redirect(url_for('backoffice.listar_clubes'))
        flash('Erro ao criar clube.', 'error')
    return render_template('backoffice/clubes/form.html', erros=[], dados={}, modo='criar')


@backoffice_bp.route('/clubes/<int:clube_id>/editar', methods=['GET', 'POST'])
@role_required('admin')
def editar_clube(clube_id: int):
    clube = Clube.get_by_id(clube_id)
    if not clube:
        flash('Clube não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_clubes'))
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['nome'])
        if erros:
            return render_template('backoffice/clubes/form.html',
                                   erros=erros, dados=dados, modo='editar', clube=clube)
        if Clube.editar(clube_id, dados):
            flash('Clube atualizado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_clubes'))
        flash('Erro ao atualizar clube.', 'error')
    return render_template('backoffice/clubes/form.html',
                           erros=[], dados=clube, modo='editar', clube=clube)


@backoffice_bp.route('/clubes/<int:clube_id>/eliminar', methods=['POST'])
@role_required('admin')
def eliminar_clube(clube_id: int):
    if Clube.eliminar(clube_id):
        flash('Clube eliminado permanentemente.', 'success')
    else:
        flash('Erro ao eliminar clube.', 'error')
    return redirect(url_for('backoffice.listar_clubes'))


@backoffice_bp.route('/clubes/<int:clube_id>/alternar', methods=['POST'])
@role_required('admin')
def alternar_estado_clube(clube_id: int):
    if Clube.alternar_estado(clube_id):
        flash('Estado do clube atualizado.', 'success')
    else:
        flash('Erro ao atualizar estado do clube.', 'error')
    return redirect(url_for('backoffice.listar_clubes'))


# ─── EVENTOS ──────────────────────────────────────────────────
@backoffice_bp.route('/eventos')
@role_required('conteudo')
def listar_eventos():
    pagina = request.args.get('pagina', 1, type=int)
    filtros = {
        'q': request.args.get('q', ''),
        'data_de': request.args.get('data_de', ''),
        'data_ate': request.args.get('data_ate', ''),
        'cidade': request.args.get('cidade', ''),
        'ordem': request.args.get('ordem', 'criado_em'),
        'dir': request.args.get('dir', 'DESC')
    }
    
    eventos, total = Evento.get_all(filtros=filtros, pagina=pagina, por_pagina=10)
    total_paginas = (total + 9) // 10
    cidades = Evento.get_cidades()
    
    return render_template('backoffice/eventos/listar.html',
                           eventos=eventos, pagina=pagina,
                           total_paginas=total_paginas, total=total, 
                           filtros=filtros, cidades=cidades)


@backoffice_bp.route('/eventos/novo', methods=['GET', 'POST'])
@role_required('conteudo')
def criar_evento():
    categorias = Categoria.get_all()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'data_evento', 'cidade', 'descricao', 'hora', 'categoria_id'])
        
        # Validação estrita da cidade (Portugal)
        if dados.get('cidade') not in MUNICIPIOS_PORTUGAL:
            erros.append(f"A cidade '{dados.get('cidade')}' não é válida em Portugal.")
        
        if erros:
            return render_template('backoffice/eventos/form.html',
                                   categorias=categorias, erros=erros, dados=dados, modo='criar')
        
        # Processar Imagem
        foto = request.files.get('imagem_ficheiro')
        if not foto or foto.filename == '':
            erros.append("A imagem do evento é obrigatória.")
        else:
            dados['imagem'] = processar_upload(foto, 'eventos')

        if erros:
            return render_template('backoffice/eventos/form.html',
                                   categorias=categorias, erros=erros, dados=dados, modo='criar')

        if Evento.criar(dados):
            flash('Evento criado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_eventos'))
        flash('Erro ao criar evento.', 'error')
    return render_template('backoffice/eventos/form.html',
                           categorias=categorias, erros=[], dados={}, modo='criar')


@backoffice_bp.route('/eventos/<int:evento_id>/editar', methods=['GET', 'POST'])
@role_required('conteudo')
def editar_evento(evento_id: int):
    evento = Evento.get_by_id(evento_id)
    if not evento:
        flash('Evento não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_eventos'))
    categorias = Categoria.get_all()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'data_evento', 'cidade', 'descricao', 'hora', 'categoria_id'])
        
        # Validação estrita da cidade (Portugal)
        if dados.get('cidade') not in MUNICIPIOS_PORTUGAL:
            erros.append(f"A cidade '{dados.get('cidade')}' não é válida em Portugal.")

        if erros:
            return render_template('backoffice/eventos/form.html',
                                   categorias=categorias, erros=erros, dados=dados, modo='editar', evento=evento)
        
        # Processar Imagem
        foto = request.files.get('imagem_ficheiro')
        if foto:
            dados['imagem'] = processar_upload(foto, 'eventos')
        else:
            dados['imagem'] = evento.get('imagem') # Manter a que já tinha

        if Evento.editar(evento_id, dados):
            flash('Evento atualizado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_eventos'))
        flash('Erro ao atualizar evento.', 'error')
    return render_template('backoffice/eventos/form.html',
                           categorias=categorias, erros=[], dados=evento, modo='editar', evento=evento)


@backoffice_bp.route('/eventos/<int:evento_id>/eliminar', methods=['POST'])
@role_required('conteudo')
def eliminar_evento(evento_id: int):
    if Evento.eliminar(evento_id):
        flash('Evento eliminado.', 'success')
    else:
        flash('Erro ao eliminar evento.', 'error')
    return redirect(url_for('backoffice.listar_eventos'))


@backoffice_bp.route('/eventos/<int:evento_id>/destaque', methods=['POST'])
@role_required('conteudo')
def toggle_destaque_evento(evento_id: int):
    """Alterna o estado de destaque de um evento (estrela on/off)."""
    if Evento.toggle_destaque(evento_id):
        flash('Estado de destaque atualizado.', 'success')
    else:
        flash('Erro ao atualizar destaque.', 'error')
    return redirect(url_for('backoffice.listar_eventos'))


# ─── NOTÍCIAS ─────────────────────────────────────────────────
@backoffice_bp.route('/noticias')
@role_required('conteudo', 'noticias')
def listar_noticias():
    pagina = request.args.get('pagina', 1, type=int)
    filtros = {
        'q': request.args.get('q', '')
    }
    noticias, total = Noticia.get_all(filtros=filtros, pagina=pagina, por_pagina=10)
    total_paginas = (total + 9) // 10
    return render_template('backoffice/noticias/listar.html',
                           noticias=noticias, pagina=pagina,
                           total_paginas=total_paginas, total=total, filtros=filtros)


@backoffice_bp.route('/noticias/novo', methods=['GET', 'POST'])
@role_required('conteudo', 'noticias')
def criar_noticia():
    categorias = Categoria.get_all()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'conteudo', 'publicado_em'])
        
        if erros:
            return render_template('backoffice/noticias/form.html',
                                   categorias=categorias, erros=erros, dados=dados, modo='criar')
        
        # Imagem
        foto = request.files.get('imagem_ficheiro')
        if foto:
            dados['imagem'] = processar_upload(foto, 'noticias')

        if Noticia.criar(dados):
            flash('Notícia criada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_noticias'))
        flash('Erro ao criar notícia.', 'error')
    return render_template('backoffice/noticias/form.html',
                           categorias=categorias, erros=[], dados={}, modo='criar')


@backoffice_bp.route('/noticias/<int:noticia_id>/editar', methods=['GET', 'POST'])
@role_required('conteudo', 'noticias')
def editar_noticia(noticia_id: int):
    noticia = Noticia.get_by_id(noticia_id)
    if not noticia:
        flash('Notícia não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_noticias'))
    categorias = Categoria.get_all()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'conteudo', 'publicado_em'])
        
        if erros:
            return render_template('backoffice/noticias/form.html',
                                   categorias=categorias, erros=erros, dados=dados, modo='editar', noticia=noticia)
        
        # Imagem
        foto = request.files.get('imagem_ficheiro')
        if foto:
            dados['imagem'] = processar_upload(foto, 'noticias')
        else:
            dados['imagem'] = noticia.get('imagem')

        if Noticia.editar(noticia_id, dados):
            flash('Notícia atualizada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_noticias'))
        flash('Erro ao atualizar notícia.', 'error')
    return render_template('backoffice/noticias/form.html',
                           categorias=categorias, erros=[], dados=noticia, modo='editar', noticia=noticia)


@backoffice_bp.route('/noticias/<int:noticia_id>/eliminar', methods=['POST'])
@role_required('conteudo', 'noticias')
def eliminar_noticia(noticia_id: int):
    if Noticia.eliminar(noticia_id):
        flash('Notícia eliminada.', 'success')
    else:
        flash('Erro ao eliminar notícia.', 'error')
    return redirect(url_for('backoffice.listar_noticias'))


# ─── CATEGORIAS ───────────────────────────────────────────────
@backoffice_bp.route('/categorias')
@role_required('conteudo')
def listar_categorias():
    categorias = Categoria.get_all()
    return render_template('backoffice/categorias/listar.html', categorias=categorias)


@backoffice_bp.route('/categorias/novo', methods=['GET', 'POST'])
@role_required('conteudo')
def criar_categoria():
    if request.method == 'POST':
        nome = request.form.get('nome', '')
        icone = request.form.get('icone', '🎭')
        cor = request.form.get('cor', '#2563eb')
        if not nome:
            flash('O nome é obrigatório.', 'error')
        elif Categoria.criar(nome, icone, cor):
            flash('Categoria criada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_categorias'))
        else:
            flash('Erro ao criar categoria.', 'error')
    return render_template('backoffice/categorias/form.html', dados={}, modo='criar')


@backoffice_bp.route('/categorias/<int:cat_id>/editar', methods=['GET', 'POST'])
@role_required('conteudo')
def editar_categoria(cat_id: int):
    categoria = Categoria.get_by_id(cat_id)
    if not categoria:
        flash('Categoria não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_categorias'))
    if request.method == 'POST':
        nome = request.form.get('nome', '')
        icone = request.form.get('icone', '🎭')
        cor = request.form.get('cor', '#2563eb')
        if not nome:
            flash('O nome é obrigatório.', 'error')
        elif Categoria.editar(cat_id, nome, icone, cor):
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_categorias'))
        else:
            flash('Erro ao atualizar categoria.', 'error')
    return render_template('backoffice/categorias/form.html', dados=categoria, modo='editar')


@backoffice_bp.route('/categorias/<int:cat_id>/eliminar', methods=['POST'])
@role_required('conteudo')
def eliminar_categoria(cat_id: int):
    if Categoria.eliminar(cat_id):
        flash('Categoria eliminada.', 'success')
    else:
        flash('Erro ao eliminar (pode ter eventos associados).', 'error')
    return redirect(url_for('backoffice.listar_categorias'))


# ─── CLUBE DE LEITURA ─────────────────────────────────────────
@backoffice_bp.route('/leitura/livros')
@role_required('leitura')
def listar_livros():
    filtros = {
        'q': request.args.get('q', ''),
        'ordem': request.args.get('ordem', 'criado_em'),
        'dir': request.args.get('dir', 'DESC')
    }
    livros = Livro.get_all(filtros=filtros)
    return render_template('backoffice/leitura/listar_livros.html', livros=livros, filtros=filtros)


@backoffice_bp.route('/leitura/livros/novo', methods=['GET', 'POST'])
@role_required('leitura')
def criar_livro():
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'autor'])
        
        if erros:
            return render_template('backoffice/leitura/form_livro.html',
                                   erros=erros, dados=dados, modo='criar')
        
        # Imagem
        foto = request.files.get('imagem_ficheiro')
        if not foto or foto.filename == '':
            erros.append("A imagem da capa é obrigatória.")
        else:
            dados['imagem'] = processar_upload(foto, 'livros')
            
        if erros:
            return render_template('backoffice/leitura/form_livro.html',
                                   erros=erros, dados=dados, modo='criar')

        if Livro.criar(dados):
            flash('Livro adicionado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_livros'))
        flash('Erro ao adicionar livro.', 'error')
    return render_template('backoffice/leitura/form_livro.html', erros=[], dados={}, modo='criar')


@backoffice_bp.route('/verificar-livro', methods=['POST'])
@role_required('leitura')
def verificar_livro():
    url = request.json.get('url')
    if not url:
        return jsonify({'erro': 'URL não fornecida'}), 400
    
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return jsonify({'disponivel': False, 'mensagem': 'Não foi possível aceder à página'})
        
        soup = BeautifulSoup(response.text, 'html.parser')
        texto_pagina = soup.get_text().lower()
        
        palavras_chave = ['disponível', 'disponivel', 'em stock', 'requisição', 'requisitar', 'disponibilidade']
        indisponivel_keywords = ['indisponível', 'indisponivel', 'esgotado', 'fora de stock']
        
        # Lógica simples de verificação
        disponivel = False
        if any(kw in texto_pagina for kw in palavras_chave):
            disponivel = True
        if any(kw in texto_pagina for kw in indisponivel_keywords):
            disponivel = False
            
        return jsonify({
            'disponivel': disponivel,
            'mensagem': 'Livro Disponível' if disponivel else 'Livro Indisponível'
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@backoffice_bp.route('/leitura/livros/<int:livro_id>/editar', methods=['GET', 'POST'])
@role_required('leitura')
def editar_livro(livro_id: int):
    livro = Livro.get_by_id(livro_id)
    if not livro:
        flash('Livro não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_livros'))
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'autor'])
        
        if erros:
            return render_template('backoffice/leitura/form_livro.html',
                                   erros=erros, dados=dados, modo='editar', livro=livro)
        
        # Imagem
        foto = request.files.get('imagem_ficheiro')
        if foto:
            dados['imagem'] = processar_upload(foto, 'livros')
        else:
            dados['imagem'] = livro.get('imagem')

        if Livro.editar(livro_id, dados):
            flash('Livro atualizado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_livros'))
        flash('Erro ao atualizar livro.', 'error')
    return render_template('backoffice/leitura/form_livro.html',
                           erros=[], dados=livro, modo='editar', livro=livro)


@backoffice_bp.route('/leitura/livros/<int:livro_id>/eliminar', methods=['POST'])
@role_required('leitura')
def eliminar_livro(livro_id: int):
    if Livro.eliminar(livro_id):
        flash('Livro eliminado.', 'success')
    else:
        flash('Erro ao eliminar livro.', 'error')
    return redirect(url_for('backoffice.listar_livros'))


@backoffice_bp.route('/leitura/livros/<int:livro_id>/destaque', methods=['POST'])
@role_required('leitura')
def toggle_destaque_livro(livro_id: int):
    """Alterna o estado de destaque de um livro."""
    if Livro.toggle_destaque(livro_id):
        flash('Estado de destaque do livro atualizado.', 'success')
    else:
        flash('Erro ao atualizar destaque.', 'error')
    return redirect(url_for('backoffice.listar_livros'))


@backoffice_bp.route('/leitura/requisicoes')
@role_required('leitura')
def listar_requisicoes():
    """Listagem global de todas as requisições de livros."""
    from app.models.livro import RequisicaoLivro
    pagina = request.args.get('pagina', 1, type=int)
    filtros = {
        'estado': request.args.get('estado', ''),
        'q': request.args.get('q', '')
    }
    
    requisicoes, total = RequisicaoLivro.get_all_paginated(filtros, pagina)
    total_paginas = (total + 20 - 1) // 20 if total > 0 else 0
    
    # Automatização: Verificar prazos e enviar lembretes silenciosamente ao listar
    try:
        RequisicaoLivro.verificar_codigos_expirados()
        RequisicaoLivro.enviar_lembretes_devolucao()
    except Exception as e:
        print(f"Erro na automatização de lembretes: {e}")
    
    return render_template('backoffice/leitura/listar_requisicoes.html',
                           requisicoes=requisicoes,
                           total=total,
                           pagina=pagina,
                           total_paginas=total_paginas,
                           filtros=filtros)


@backoffice_bp.route('/leitura/livros/<int:livro_id>/requisicoes')
@role_required('leitura')
def requisicoes_livro(livro_id: int):
    from app.models.livro import RequisicaoLivro
    livro = Livro.get_by_id(livro_id)
    if not livro:
        flash('Livro não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_livros'))
        
    requisicoes = RequisicaoLivro.get_by_livro(livro_id)
    
    return render_template('backoffice/leitura/requisicoes_livro.html', 
                           livro=livro, 
                           requisicoes=requisicoes)


@backoffice_bp.route('/leitura/requisicoes/<int:req_id>/estado', methods=['POST'])
@role_required('leitura')
def atualizar_requisicao_estado(req_id: int):
    """Atualiza o estado de uma requisição de livro e envia email."""
    from app.models.livro import RequisicaoLivro
    from app.utils.email import EmailService
    novo_estado = request.form.get('novo_estado')
    
    if not novo_estado:
        flash('Estado inválido.', 'error')
        return redirect(request.referrer or url_for('backoffice.listar_livros'))
    
    # Buscar dados da requisição antes de atualizar
    requisicao = RequisicaoLivro.get_by_id(req_id)
    
    if RequisicaoLivro.atualizar_estado(req_id, novo_estado):
        flash(f'Requisição atualizada para {novo_estado}.', 'success')
        
        # Enviar email baseado na decisão do admin
        if requisicao:
            email = requisicao.get('email', '')
            nome = requisicao.get('nome', '')
            codigo = requisicao.get('codigo', '')
            livro_titulo = requisicao.get('livro_titulo', requisicao.get('titulo', 'Livro'))
            
            if novo_estado in ('Aceite',):
                # Admin aprovou → enviar código de levantamento
                EmailService.enviar_confirmacao_requisicao_livro(email, nome, livro_titulo, codigo)
            elif novo_estado in ('Recusado',):
                # Admin recusou → enviar email de recusa
                EmailService.enviar_requisicao_recusada(email, nome, livro_titulo)
    else:
        flash('Erro ao atualizar requisição.', 'error')
        
    return redirect(request.referrer or url_for('backoffice.listar_livros'))


@backoffice_bp.route('/leitura/livros/<int:livro_id>/requisicao-presencial', methods=['POST'])
@role_required('leitura')
def requisicao_presencial(livro_id: int):
    """Cria uma requisição presencial (admin regista em nome do aluno)."""
    from app.models.livro import RequisicaoLivro
    livro = Livro.get_by_id(livro_id)
    if not livro:
        flash('Livro não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_livros'))
    
    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip()
    
    if not nome or not email:
        flash('Preencha o nome e email do aluno.', 'error')
        return redirect(url_for('backoffice.requisicoes_livro', livro_id=livro_id))
    
    dados = {
        'livro_id': livro_id,
        'nome': nome,
        'email': email
    }
    
    codigo = RequisicaoLivro.criar(dados)
    
    if codigo:
        # Auto-aprovar — buscar o ID da requisição e atualizar estado
        reqs = RequisicaoLivro.get_by_livro(livro_id)
        for r in reqs:
            if r.get('codigo_requisicao') == codigo:
                RequisicaoLivro.atualizar_estado(r['id'], 'Aceite')
                break
        
        flash(f'Requisição presencial registada! Código: {codigo}', 'success')
    else:
        flash('Erro ao registar a requisição.', 'error')
    
    return redirect(url_for('backoffice.requisicoes_livro', livro_id=livro_id))




@backoffice_bp.route('/leitura/requisicoes/confirmar-levantamento', methods=['POST'])
@role_required('leitura')
def confirmar_levantamento():
    """Admin insere o código para confirmar que o aluno levantou o livro."""
    from app.models.livro import RequisicaoLivro
    codigo = request.form.get('codigo', '').strip()
    
    if not codigo:
        flash('Insira um código de requisição.', 'error')
        return redirect(url_for('backoffice.listar_requisicoes'))
    
    resultado = RequisicaoLivro.confirmar_levantamento(codigo)
    
    if resultado['ok']:
        req = resultado['requisicao']
        flash(f'Levantamento confirmado! Livro "{req.get("livro_titulo", "")}" entregue a {req.get("nome_aluno", "")}. Prazo: 7 dias.', 'success')
    else:
        flash(resultado['erro'], 'error')
        
    return redirect(url_for('backoffice.listar_requisicoes'))

@backoffice_bp.route('/leitura/sessoes')
@role_required('leitura')
def listar_sessoes():
    filtros = {
        'q': request.args.get('q', ''),
        'livro_id': request.args.get('livro_id'),
        'data_de': request.args.get('data_de'),
        'data_ate': request.args.get('data_ate'),
        'ordem': request.args.get('ordem', 'criado_em'),
        'dir': request.args.get('dir', 'DESC')
    }
    sessoes = SessaoLeitura.get_calendario(filtros=filtros)
    livros = Livro.get_all()
    return render_template('backoffice/leitura/listar_sessoes.html', sessoes=sessoes, livros=livros, filtros=filtros)


@backoffice_bp.route('/leitura/sessoes/novo', methods=['GET', 'POST'])
@role_required('leitura')
def criar_sessao():
    livros = Livro.get_all()
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['data_sessao', 'tema'])
        if erros:
            return render_template('backoffice/leitura/form_sessao.html',
                                   livros=livros, erros=erros, dados=dados, modo='criar')
        if SessaoLeitura.criar(dados):
            flash('Sessão criada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_sessoes'))
        flash('Erro ao criar sessão.', 'error')
    return render_template('backoffice/leitura/form_sessao.html',
                           livros=livros, erros=[], dados={}, modo='criar')


@backoffice_bp.route('/leitura/sessoes/<int:sessao_id>/editar', methods=['GET', 'POST'])
@role_required('leitura')
def editar_sessao(sessao_id: int):
    sessao = SessaoLeitura.get_by_id(sessao_id)
    livros = Livro.get_all()
    if not sessao:
        flash('Sessão não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_sessoes'))
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['data_sessao', 'tema'])
        if erros:
            return render_template('backoffice/leitura/form_sessao.html',
                                   livros=livros, erros=erros, dados=dados, modo='editar', sessao=sessao)
        if SessaoLeitura.editar(sessao_id, dados):
            flash('Sessão atualizada!', 'success')
            return redirect(url_for('backoffice.listar_sessoes'))
        flash('Erro ao atualizar sessão.', 'error')
    return render_template('backoffice/leitura/form_sessao.html',
                           livros=livros, erros=[], dados=sessao, modo='editar', sessao=sessao)


@backoffice_bp.route('/leitura/sessoes/<int:sessao_id>/eliminar', methods=['POST'])
@role_required('leitura')
def eliminar_sessao(sessao_id: int):
    if SessaoLeitura.eliminar(sessao_id):
        flash('Sessão eliminada.', 'success')
    else:
        flash('Erro ao eliminar sessão.', 'error')
    return redirect(url_for('backoffice.listar_sessoes'))

@backoffice_bp.route('/leitura/sessoes/<int:sessao_id>/inscricoes')
@role_required('leitura')
def inscricoes_sessao(sessao_id: int):
    from app.models.livro import InscricaoLeitura
    sessao = SessaoLeitura.get_by_id(sessao_id)
    if not sessao:
        flash('Sessão não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_sessoes'))
        
    inscricoes = InscricaoLeitura.get_inscricoes_by_sessao(sessao_id)
    
    return render_template('backoffice/leitura/inscricoes_sessao.html', 
                           sessao=sessao, 
                           inscricoes=inscricoes)

@backoffice_bp.route('/leitura/membros')
@role_required('leitura')
def listar_membros_leitura():
    from app.models.livro import MembroLeitura
    membros = MembroLeitura.get_all()
    return render_template('backoffice/leitura/membros.html', membros=membros)

@backoffice_bp.route('/leitura/membros/<int:membro_id>/acao', methods=['POST'])
@role_required('leitura')
def acao_membro_leitura(membro_id: int):
    from app.models.livro import MembroLeitura
    from app.utils.email import EmailService
    
    acao = request.form.get('acao') # 'Aceite' ou 'Recusado'
    if acao not in ['Aceite', 'Recusado']:
        flash('Ação inválida.', 'error')
        return redirect(url_for('backoffice.listar_membros_leitura'))
        
    membro = MembroLeitura.get_by_id(membro_id)
    if not membro:
        flash('Membro não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_membros_leitura'))
        
    if MembroLeitura.atualizar_estado(membro_id, acao):
        EmailService.enviar_resposta_membro_leitura(membro['email'], membro['nome'], acao)
        flash(f'Membro marcado como {acao} e e-mail enviado.', 'success')
    else:
        flash('Erro ao atualizar estado.', 'error')
        
    return redirect(url_for('backoffice.listar_membros_leitura'))

# ─── CLUBE DE TEATRO ──────────────────────────────────────────
@backoffice_bp.route('/teatro')
@role_required('teatro')
def listar_espetaculos():
    filtros = {
        'q': request.args.get('q', ''),
        'tipo': request.args.get('tipo', ''),
        'data_de': request.args.get('data_de', ''),
        'data_ate': request.args.get('data_ate', ''),
        'ordem': request.args.get('ordem', 'criado_em'),
        'dir': request.args.get('dir', 'DESC')
    }
    espetaculos = Espetaculo.get_agenda(filtros=filtros)
    return render_template('backoffice/teatro/listar.html', espetaculos=espetaculos, filtros=filtros)

@backoffice_bp.route('/teatro/membros')
@role_required('teatro')
def listar_membros_teatro():
    from app.models.espetaculo import MembroTeatro
    membros = MembroTeatro.get_all()
    return render_template('backoffice/teatro/membros.html', membros=membros)


@backoffice_bp.route('/teatro/membros/<int:membro_id>/acao', methods=['POST'])
@role_required('teatro')
def acao_membro_teatro(membro_id: int):
    from app.models.espetaculo import MembroTeatro
    from app.utils.email import EmailService
    
    acao = request.form.get('acao') # 'Aceite' ou 'Recusado'
    if acao not in ['Aceite', 'Recusado']:
        flash('Ação inválida.', 'error')
        return redirect(url_for('backoffice.listar_membros_teatro'))
        
    membro = MembroTeatro.get_by_id(membro_id)
    if not membro:
        flash('Membro não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_membros_teatro'))
        
    if MembroTeatro.atualizar_estado(membro_id, acao):
        # Enviar email
        EmailService.enviar_resposta_membro(membro['email'], membro['nome'], acao)
        flash(f'Membro marcado como {acao} e e-mail enviado.', 'success')
    else:
        flash('Erro ao atualizar estado.', 'error')
        
    return redirect(url_for('backoffice.listar_membros_teatro'))


@backoffice_bp.route('/teatro/novo', methods=['GET', 'POST'])
@role_required('teatro')
def criar_espetaculo():
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'data_evento', 'tipo', 'descricao', 'hora'])
        
        if erros:
            return render_template('backoffice/teatro/form.html',
                                   erros=erros, dados=dados, modo='criar')
        
        # Imagem
        foto = request.files.get('imagem_ficheiro')
        if not foto or foto.filename == '':
            erros.append("A imagem do espetáculo é obrigatória.")
        else:
            dados['imagem'] = processar_upload(foto, 'espetaculos')
            
        if erros:
            return render_template('backoffice/teatro/form.html',
                                   erros=erros, dados=dados, modo='criar')

        if Espetaculo.criar(dados):
            flash('Espetáculo criado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_espetaculos'))
        flash('Erro ao criar espetáculo.', 'error')
    return render_template('backoffice/teatro/form.html', erros=[], dados={}, modo='criar')


@backoffice_bp.route('/teatro/<int:esp_id>/editar', methods=['GET', 'POST'])
@role_required('teatro')
def editar_espetaculo(esp_id: int):
    espetaculo = Espetaculo.get_by_id(esp_id)
    if not espetaculo:
        flash('Espetáculo não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos'))
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'data_evento', 'tipo', 'descricao', 'hora'])
        
        if erros:
            return render_template('backoffice/teatro/form.html',
                                   erros=erros, dados=dados, modo='editar', espetaculo=espetaculo)
        
        # Imagem
        foto = request.files.get('imagem_ficheiro')
        if foto:
            dados['imagem'] = processar_upload(foto, 'espetaculos')
        else:
            dados['imagem'] = espetaculo.get('imagem')

        if Espetaculo.editar(esp_id, dados):
            flash('Espetáculo atualizado com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_espetaculos'))
        flash('Erro ao atualizar espetáculo.', 'error')
    return render_template('backoffice/teatro/form.html',
                           erros=[], dados=espetaculo, modo='editar', espetaculo=espetaculo)


@backoffice_bp.route('/teatro/<int:esp_id>/eliminar', methods=['POST'])
@role_required('teatro')
def eliminar_espetaculo(esp_id: int):
    if Espetaculo.eliminar(esp_id):
        flash('Espetáculo eliminado.', 'success')
    else:
        flash('Erro ao eliminar espetáculo.', 'error')
    return redirect(url_for('backoffice.listar_espetaculos'))


@backoffice_bp.route('/teatro/<int:esp_id>/destaque', methods=['POST'])
@role_required('teatro')
def toggle_destaque_espetaculo(esp_id: int):
    """Alterna o estado de destaque de um espetáculo."""
    if Espetaculo.toggle_destaque(esp_id):
        flash('Estado de destaque do espetáculo atualizado.', 'success')
    else:
        flash('Erro ao atualizar destaque.', 'error')
    return redirect(url_for('backoffice.listar_espetaculos'))


@backoffice_bp.route('/teatro/<int:esp_id>/reservas')
@role_required('teatro')
def reservas_espetaculo(esp_id: int):
    from app.models.inscricao_teatro import InscricaoTeatro
    espetaculo = Espetaculo.get_by_id(esp_id)
    if not espetaculo:
        flash('Espetáculo não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos'))
        
    inscricoes = InscricaoTeatro.get_inscricoes_by_espetaculo(esp_id)
    
    return render_template('backoffice/teatro/reservas.html', 
                           espetaculo=espetaculo, 
                           inscricoes=inscricoes)


@backoffice_bp.route('/teatro/<int:esp_id>/galeria')
@role_required('teatro')
def galeria_espetaculo(esp_id: int):
    """Gerir galeria de fotos de um espetáculo."""
    espetaculo = Espetaculo.get_by_id(esp_id)
    if not espetaculo:
        flash('Espetáculo não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos'))
    
    fotos = Espetaculo.get_fotos_by_espetaculo(esp_id)
    return render_template('backoffice/teatro/galeria.html',
                           espetaculo=espetaculo, fotos=fotos)


@backoffice_bp.route('/teatro/<int:esp_id>/galeria/adicionar', methods=['POST'])
@role_required('teatro')
def adicionar_foto_espetaculo(esp_id: int):
    """Adicionar foto à galeria de um espetáculo."""
    espetaculo = Espetaculo.get_by_id(esp_id)
    if not espetaculo:
        flash('Espetáculo não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos'))
    
    titulo = request.form.get('titulo', espetaculo['titulo'])
    foto = request.files.get('imagem_ficheiro')
    
    if not foto or foto.filename == '':
        flash('Selecione uma imagem para adicionar.', 'error')
        return redirect(url_for('backoffice.galeria_espetaculo', esp_id=esp_id))
    
    caminho = processar_upload(foto, 'galeria_teatro')
    if caminho:
        if Espetaculo.adicionar_foto_galeria(esp_id, titulo, caminho):
            flash('Foto adicionada à galeria com sucesso!', 'success')
        else:
            flash('Erro ao guardar a foto na base de dados.', 'error')
    else:
        flash('Formato de imagem não suportado.', 'error')
    
    return redirect(url_for('backoffice.galeria_espetaculo', esp_id=esp_id))


@backoffice_bp.route('/teatro/galeria/<int:foto_id>/eliminar', methods=['POST'])
@role_required('teatro')
def eliminar_foto_espetaculo(foto_id: int):
    """Eliminar uma foto da galeria."""
    esp_id = request.form.get('esp_id', 0, type=int)
    if Espetaculo.eliminar_foto_galeria(foto_id):
        flash('Foto removida da galeria.', 'success')
    else:
        flash('Erro ao eliminar foto.', 'error')
    return redirect(url_for('backoffice.galeria_espetaculo', esp_id=esp_id))


# ─── TUNA ACADÉMICA ───────────────────────────────────────────
@backoffice_bp.route('/tuna')
@role_required('tuna')
def listar_espetaculos_tuna():
    from app.models.tuna import EspetaculoTuna
    filtros = {
        'q': request.args.get('q', ''),
        'tipo': request.args.get('tipo', ''),
        'data_de': request.args.get('data_de', ''),
        'data_ate': request.args.get('data_ate', ''),
        'ordem': request.args.get('ordem', 'criado_em'),
        'dir': request.args.get('dir', 'DESC')
    }
    espetaculos = EspetaculoTuna.get_agenda(filtros=filtros)
    return render_template('backoffice/tuna/listar.html', espetaculos=espetaculos, filtros=filtros)


@backoffice_bp.route('/tuna/membros')
@role_required('tuna')
def listar_membros_tuna():
    from app.models.tuna import MembroTuna
    membros = MembroTuna.get_all()
    return render_template('backoffice/tuna/membros.html', membros=membros)


@backoffice_bp.route('/tuna/membros/<int:membro_id>/acao', methods=['POST'])
@role_required('tuna')
def acao_membro_tuna(membro_id: int):
    from app.models.tuna import MembroTuna
    from app.utils.email import EmailService
    
    acao = request.form.get('acao')
    if acao not in ['Aceite', 'Recusado']:
        flash('Ação inválida.', 'error')
        return redirect(url_for('backoffice.listar_membros_tuna'))
        
    membro = MembroTuna.get_by_id(membro_id)
    if not membro:
        flash('Membro não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_membros_tuna'))
        
    if MembroTuna.atualizar_estado(membro_id, acao):
        EmailService.enviar_resposta_membro_tuna(membro['email'], membro['nome'], acao)
        flash(f'Membro marcado como {acao} e e-mail enviado.', 'success')
    else:
        flash('Erro ao atualizar estado.', 'error')
        
    return redirect(url_for('backoffice.listar_membros_tuna'))


@backoffice_bp.route('/tuna/novo', methods=['GET', 'POST'])
@role_required('tuna')
def criar_espetaculo_tuna():
    from app.models.tuna import EspetaculoTuna
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'data_evento', 'tipo', 'descricao', 'hora'])
        
        if erros:
            return render_template('backoffice/tuna/form.html',
                                   erros=erros, dados=dados, modo='criar')
        
        foto = request.files.get('imagem_ficheiro')
        if not foto or foto.filename == '':
            erros.append("A imagem da atuação é obrigatória.")
        else:
            dados['imagem'] = processar_upload(foto, 'tuna')
            
        if erros:
            return render_template('backoffice/tuna/form.html',
                                   erros=erros, dados=dados, modo='criar')

        if EspetaculoTuna.criar(dados):
            flash('Atuação criada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_espetaculos_tuna'))
        flash('Erro ao criar atuação.', 'error')
    return render_template('backoffice/tuna/form.html', erros=[], dados={}, modo='criar')


@backoffice_bp.route('/tuna/<int:esp_id>/editar', methods=['GET', 'POST'])
@role_required('tuna')
def editar_espetaculo_tuna(esp_id: int):
    from app.models.tuna import EspetaculoTuna
    espetaculo = EspetaculoTuna.get_by_id(esp_id)
    if not espetaculo:
        flash('Atuação não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos_tuna'))
    if request.method == 'POST':
        dados = request.form.to_dict()
        erros = validar_campos(dados, ['titulo', 'data_evento', 'tipo', 'descricao', 'hora'])
        
        if erros:
            return render_template('backoffice/tuna/form.html',
                                   erros=erros, dados=dados, modo='editar', espetaculo=espetaculo)
        
        foto = request.files.get('imagem_ficheiro')
        if foto:
            dados['imagem'] = processar_upload(foto, 'tuna')
        else:
            dados['imagem'] = espetaculo.get('imagem')

        if EspetaculoTuna.editar(esp_id, dados):
            flash('Atuação atualizada com sucesso!', 'success')
            return redirect(url_for('backoffice.listar_espetaculos_tuna'))
        flash('Erro ao atualizar atuação.', 'error')
    return render_template('backoffice/tuna/form.html',
                           erros=[], dados=espetaculo, modo='editar', espetaculo=espetaculo)


@backoffice_bp.route('/tuna/<int:esp_id>/eliminar', methods=['POST'])
@role_required('tuna')
def eliminar_espetaculo_tuna(esp_id: int):
    from app.models.tuna import EspetaculoTuna
    if EspetaculoTuna.eliminar(esp_id):
        flash('Atuação eliminada.', 'success')
    else:
        flash('Erro ao eliminar atuação.', 'error')
    return redirect(url_for('backoffice.listar_espetaculos_tuna'))


@backoffice_bp.route('/tuna/<int:esp_id>/destaque', methods=['POST'])
@role_required('tuna')
def toggle_destaque_tuna(esp_id: int):
    from app.models.tuna import EspetaculoTuna
    if EspetaculoTuna.toggle_destaque(esp_id):
        flash('Estado de destaque atualizado.', 'success')
    else:
        flash('Erro ao atualizar destaque.', 'error')
    return redirect(url_for('backoffice.listar_espetaculos_tuna'))


@backoffice_bp.route('/tuna/<int:esp_id>/galeria')
@role_required('tuna')
def galeria_tuna(esp_id: int):
    from app.models.tuna import EspetaculoTuna
    espetaculo = EspetaculoTuna.get_by_id(esp_id)
    if not espetaculo:
        flash('Atuação não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos_tuna'))
    
    fotos = EspetaculoTuna.get_fotos_by_espetaculo(esp_id)
    return render_template('backoffice/tuna/galeria.html',
                           espetaculo=espetaculo, fotos=fotos)


@backoffice_bp.route('/tuna/<int:esp_id>/galeria/adicionar', methods=['POST'])
@role_required('tuna')
def adicionar_foto_tuna(esp_id: int):
    from app.models.tuna import EspetaculoTuna
    espetaculo = EspetaculoTuna.get_by_id(esp_id)
    if not espetaculo:
        flash('Atuação não encontrada.', 'error')
        return redirect(url_for('backoffice.listar_espetaculos_tuna'))
    
    titulo = request.form.get('titulo', espetaculo['titulo'])
    foto = request.files.get('imagem_ficheiro')
    
    if not foto or foto.filename == '':
        flash('Selecione uma imagem para adicionar.', 'error')
        return redirect(url_for('backoffice.galeria_tuna', esp_id=esp_id))
    
    caminho = processar_upload(foto, 'galeria_tuna')
    if caminho:
        if EspetaculoTuna.adicionar_foto_galeria(esp_id, titulo, caminho):
            flash('Foto adicionada à galeria com sucesso!', 'success')
        else:
            flash('Erro ao guardar a foto na base de dados.', 'error')
    else:
        flash('Formato de imagem não suportado.', 'error')
    
    return redirect(url_for('backoffice.galeria_tuna', esp_id=esp_id))


@backoffice_bp.route('/tuna/galeria/<int:foto_id>/eliminar', methods=['POST'])
@role_required('tuna')
def eliminar_foto_tuna(foto_id: int):
    from app.models.tuna import EspetaculoTuna
    esp_id = request.form.get('esp_id', 0, type=int)
    if EspetaculoTuna.eliminar_foto_galeria(foto_id):
        flash('Foto removida da galeria.', 'success')
    else:
        flash('Erro ao eliminar foto.', 'error')
    return redirect(url_for('backoffice.galeria_tuna', esp_id=esp_id))


# ─── EXPORTAÇÃO EXCEL POR EVENTO ──────────────────────────────
@backoffice_bp.route('/eventos/<int:evento_id>/exportar')
@role_required('conteudo')
def exportar_evento_excel(evento_id: int):
    """Gera um ficheiro Excel (.xlsx) formatado com as inscrições de um evento."""
    from app import get_db
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    evento = Evento.get_by_id(evento_id)
    if not evento:
        flash('Evento não encontrado.', 'error')
        return redirect(url_for('backoffice.listar_eventos'))

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """SELECT ie.nome, ie.email, ie.codigo, ie.valor_pago, ie.criado_em
               FROM inscricoes_eventos ie
               WHERE ie.evento_id = ?
               ORDER BY ie.criado_em ASC""",
            (evento_id,)
        )
        inscricoes = cursor.fetchall()

    # ── Criar Workbook ──
    wb = Workbook()
    ws = wb.active
    ws.title = "Inscrições"

    # ── Cores e Estilos ──
    LARANJA = 'F97316'
    LARANJA_CLARO = 'FFF7ED'
    CINZA_HEADER = '374151'
    VERDE = '059669'
    BRANCO = 'FFFFFF'

    font_titulo = Font(name='Calibri', size=16, bold=True, color=BRANCO)
    font_subtitulo = Font(name='Calibri', size=10, color='FFD9B3')
    font_header = Font(name='Calibri', size=11, bold=True, color=BRANCO)
    font_normal = Font(name='Calibri', size=10, color='333333')
    font_meta_label = Font(name='Calibri', size=9, bold=True, color='888888')
    font_meta_value = Font(name='Calibri', size=10, bold=True, color='333333')
    font_total = Font(name='Calibri', size=11, bold=True, color=VERDE)

    fill_header_bar = PatternFill(start_color=LARANJA, end_color=LARANJA, fill_type='solid')
    fill_col_header = PatternFill(start_color=CINZA_HEADER, end_color=CINZA_HEADER, fill_type='solid')
    fill_row_par = PatternFill(start_color=LARANJA_CLARO, end_color=LARANJA_CLARO, fill_type='solid')
    fill_row_impar = PatternFill(start_color=BRANCO, end_color=BRANCO, fill_type='solid')
    fill_total = PatternFill(start_color='ECFDF5', end_color='ECFDF5', fill_type='solid')

    thin_border = Border(
        bottom=Side(style='thin', color='E5E7EB')
    )
    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')

    # Larguras das colunas
    col_widths = [6, 30, 32, 16, 14, 22]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── Barra de Título (merge A1:F2) ──
    ws.merge_cells('A1:F2')
    cell_titulo = ws['A1']
    cell_titulo.value = f"📋  {evento['titulo']}"
    cell_titulo.font = font_titulo
    cell_titulo.fill = fill_header_bar
    cell_titulo.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    # Preencher todas as células merged
    for row in ws.iter_rows(min_row=1, max_row=2, min_col=1, max_col=6):
        for cell in row:
            cell.fill = fill_header_bar

    # ── Subtítulo (merge A3:F3) ──
    ws.merge_cells('A3:F3')
    cell_sub = ws['A3']
    cell_sub.value = "BILHETEIRA LAB CULTURAL · ISPGAYA"
    cell_sub.font = font_subtitulo
    cell_sub.fill = fill_header_bar
    cell_sub.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    for cell in ws[3]:
        cell.fill = fill_header_bar

    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 22
    ws.row_dimensions[3].height = 20

    # ── Metadados do Evento (linhas 5-7) ──
    meta_items = [
        ('Data:', evento['data_evento'].strftime('%d/%m/%Y') if evento.get('data_evento') else '—',
         'Local:', evento.get('local') or evento.get('cidade') or '—'),
        ('Tipo Ingresso:', 'Pago' if evento.get('tipo_ingresso') == 'pago' else 'Grátis',
         'Preço:', f"{float(evento.get('preco') or 0):.2f} €"),
        ('Limite Bilhetes:', str(evento.get('limite_bilhetes') or 'Sem limite'),
         'Total Inscrições:', str(len(inscricoes))),
    ]

    for i, (l1, v1, l2, v2) in enumerate(meta_items, 5):
        ws.row_dimensions[i].height = 20
        ws.cell(row=i, column=1, value=l1).font = font_meta_label
        ws.cell(row=i, column=2, value=v1).font = font_meta_value
        ws.cell(row=i, column=4, value=l2).font = font_meta_label
        ws.cell(row=i, column=5, value=v2).font = font_meta_value

    # ── Cabeçalhos da Tabela (linha 9) ──
    headers = ['#', 'Nome', 'E-mail', 'Código', 'Valor (€)', 'Data Inscrição']
    header_row = 9
    ws.row_dimensions[header_row].height = 28

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=h)
        cell.font = font_header
        cell.fill = fill_col_header
        cell.alignment = align_center if col in (1, 4, 5) else align_left

    # ── Dados das Inscrições ──
    total_receita = 0
    for idx, insc in enumerate(inscricoes, 1):
        row = header_row + idx
        ws.row_dimensions[row].height = 24
        fill = fill_row_par if idx % 2 == 0 else fill_row_impar

        valor = float(insc.get('valor_pago') or 0)
        total_receita += valor

        data_insc = insc['criado_em']
        if hasattr(data_insc, 'strftime'):
            data_str = data_insc.strftime('%d/%m/%Y %H:%M')
        else:
            data_str = str(data_insc)

        row_data = [
            idx,
            insc['nome'],
            insc['email'],
            insc['codigo'],
            f"{valor:.2f}",
            data_str
        ]

        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = font_normal
            cell.fill = fill
            cell.border = thin_border
            cell.alignment = align_center if col in (1, 4, 5) else align_left

    # ── Linha de Total ──
    total_row = header_row + len(inscricoes) + 1
    ws.row_dimensions[total_row].height = 28

    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=4)
    cell_total_label = ws.cell(row=total_row, column=1, value='RECEITA TOTAL')
    cell_total_label.font = font_total
    cell_total_label.fill = fill_total
    cell_total_label.alignment = Alignment(horizontal='right', vertical='center')
    for c in range(2, 5):
        ws.cell(row=total_row, column=c).fill = fill_total

    cell_total_val = ws.cell(row=total_row, column=5, value=f"{total_receita:.2f} €")
    cell_total_val.font = font_total
    cell_total_val.fill = fill_total
    cell_total_val.alignment = align_center

    ws.cell(row=total_row, column=6).fill = fill_total

    # ── Gerar ficheiro em memória ──
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    nome_ficheiro = f"Inscricoes_{evento['titulo'][:30].replace(' ', '_')}.xlsx"

    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{nome_ficheiro}"'}
    )


# ─── GRÁFICO DE VENDAS POR EVENTO ───────────────────────────
@backoffice_bp.route('/evento/<int:evento_id>/grafico')
@role_required('conteudo')
def grafico_evento(evento_id: int):
    """Gera um gráfico de vendas simples e direto ao ponto."""
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from app import get_db

    evento = Evento.get_by_id(evento_id)
    if not evento:
        return jsonify({'erro': 'Evento não encontrado.'}), 404

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT DATE(criado_em) AS data, valor_pago AS total FROM inscricoes_eventos WHERE evento_id = ? ORDER BY criado_em ASC",
            (evento_id,)
        )
        rows = cursor.fetchall()

    if not rows:
        return jsonify({'erro': 'Sem inscrições para este evento.'}), 200

    df = pd.DataFrame(rows)
    df['data'] = pd.to_datetime(df['data'])
    
    # Agrupar por dia (garante datas únicas)
    df_diario = df.groupby('data').agg({'total': ['count', 'sum']})
    df_diario.columns = ['qtd', 'receita']
    
    # Mostrar apenas os últimos 7 dias de atividade
    df_diario = df_diario.tail(7)

    # Gerar Gráfico de Colunas Simples
    plt.figure(figsize=(9, 4), facecolor='white')
    ax = plt.gca()
    ax.set_facecolor('white')
    
    # Converter o índice para strings formatadas para evitar que o matplotlib tente preencher dias vazios
    datas_str = [d.strftime('%d/%m') for d in df_diario.index]
    
    # Colunas de quantidade
    bars = ax.bar(datas_str, df_diario['qtd'], color='#F97316', width=0.6)
    
    # Adicionar os números por cima das colunas
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#333')

    # Estilo minimalista
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#EEE')
    ax.spines['bottom'].set_color('#EEE')
    
    ax.set_ylabel('Bilhetes Vendidos', color='#888', fontsize=9)
    plt.title(f"Vendas nos Últimos 7 Dias: {evento['titulo']}", pad=20, fontsize=11, fontweight='bold', color='#333')
    
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    return jsonify({
        'imagem': img_base64,
        'total_inscricoes': len(rows),
        'receita_total': f"{df['total'].sum():.2f}"
    })


# ─── ESQUEMA DA BASE DE DADOS (ERD) ──────────────────────────
@backoffice_bp.route('/esquema-bd')
@role_required('admin')
def esquema_bd():
    """Gera dinamicamente o ERD a partir do esquema real da BD SQLite."""
    db = get_db()

    def get_specific_id_name(table_name):
        mapping = {
            'locais': 'id_local',
            'categorias': 'id_categoria',
            'clubes': 'id_clube',
            'membros_leitura': 'id_membro_leitura',
            'membros_teatro': 'id_membro_teatro',
            'membros_tuna': 'id_membro_tuna',
            'utilizadores': 'id_utilizador',
            'livros': 'id_livro',
            'sessoes_leitura': 'id_sessao_leitura',
            'requisicoes_livros': 'id_requisicao_livro',
            'inscricoes_leitura': 'id_inscricao_leitura',
            'livro_autores': 'id_livro_autor',
            'espetaculos': 'id_espetaculo',
            'galeria_teatro': 'id_galeria_teatro',
            'inscricoes_teatro': 'id_inscricao_teatro',
            'espetaculo_equipa': 'id_espetaculo_equipa',
            'entidades_culturais': 'id_entidade_cultural',
            'espetaculos_tuna': 'id_espetaculo_tuna',
            'galeria_tuna': 'id_galeria_tuna',
            'eventos': 'id_evento',
            'galeria_eventos': 'id_galeria_evento',
            'inscricoes_eventos': 'id_inscricao_evento',
            'noticias': 'id_noticia',
            'mensagens_contacto': 'id_mensagem_contacto'
        }
        return mapping.get(table_name, f'id_{table_name}')

    # Classificação de tabelas por módulo (cor + ícone)
    TABLE_MODULES = {
        'locais':              {'color': '#5DCAA5', 'icon': 'fa-map-marker-alt', 'group': 'Núcleo'},
        'categorias':          {'color': '#5DCAA5', 'icon': 'fa-tags',          'group': 'Núcleo'},
        'clubes':              {'color': '#7F77DD', 'icon': 'fa-users',         'group': 'Clubes'},
        'membros_leitura':     {'color': '#7F77DD', 'icon': 'fa-user',          'group': 'Clubes'},
        'membros_teatro':      {'color': '#7F77DD', 'icon': 'fa-user',          'group': 'Clubes'},
        'membros_tuna':        {'color': '#7F77DD', 'icon': 'fa-user',          'group': 'Clubes'},
        'utilizadores':        {'color': '#7F77DD', 'icon': 'fa-user-shield',   'group': 'Clubes'},
        'livros':              {'color': '#3B8BD4', 'icon': 'fa-book',          'group': 'Leitura'},
        'sessoes_leitura':     {'color': '#3B8BD4', 'icon': 'fa-calendar',      'group': 'Leitura'},
        'requisicoes_livros':  {'color': '#3B8BD4', 'icon': 'fa-clipboard-list','group': 'Leitura'},
        'inscricoes_leitura':  {'color': '#3B8BD4', 'icon': 'fa-pen',           'group': 'Leitura'},
        'livro_autores':       {'color': '#3B8BD4', 'icon': 'fa-link',          'group': 'Leitura'},
        'espetaculos':         {'color': '#D85A30', 'icon': 'fa-theater-masks', 'group': 'Teatro'},
        'galeria_teatro':      {'color': '#D85A30', 'icon': 'fa-images',        'group': 'Teatro'},
        'inscricoes_teatro':   {'color': '#D85A30', 'icon': 'fa-ticket-alt',    'group': 'Teatro'},
        'espetaculo_equipa':   {'color': '#D85A30', 'icon': 'fa-users-cog',     'group': 'Teatro'},
        'entidades_culturais': {'color': '#D85A30', 'icon': 'fa-star',          'group': 'Teatro'},
        'espetaculos_tuna':    {'color': '#E6A020', 'icon': 'fa-music',         'group': 'Tuna'},
        'galeria_tuna':        {'color': '#E6A020', 'icon': 'fa-images',        'group': 'Tuna'},
        'eventos':             {'color': '#D4537E', 'icon': 'fa-calendar-alt',  'group': 'Eventos'},
        'galeria_eventos':     {'color': '#D4537E', 'icon': 'fa-images',        'group': 'Eventos'},
        'inscricoes_eventos':  {'color': '#D4537E', 'icon': 'fa-pen',           'group': 'Eventos'},
        'noticias':            {'color': '#888780', 'icon': 'fa-newspaper',     'group': 'Outros'},
        'mensagens_contacto':  {'color': '#888780', 'icon': 'fa-envelope',      'group': 'Outros'},
    }
    DEFAULT_MOD = {'color': '#888780', 'icon': 'fa-table', 'group': 'Outros'}

    with db.cursor() as cursor:
        cursor.execute("PRAGMA user_version")
        res = cursor.fetchone()
        db_version = res[0] if isinstance(res, tuple) else res['user_version']

        # 1. Obter todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        table_names = [r['name'] for r in cursor.fetchall()]

        tabelas = []
        all_fks = []  # (from_table, from_col, to_table, to_col)
        total_colunas = 0
        total_pks = 0

        for tname in table_names:
            mod = TABLE_MODULES.get(tname, DEFAULT_MOD)

            cursor.execute(f'PRAGMA table_info({tname})')
            cols_raw = cursor.fetchall()

            cursor.execute(f'PRAGMA foreign_key_list({tname})')
            fks_raw = cursor.fetchall()

            fk_map = {}
            for fk in fks_raw:
                fk_map[fk['from']] = f"{fk['table']}.{fk['to']}"
                all_fks.append((tname, fk['from'], fk['table'], fk['to']))

            # Smart implicit FK mapping (detect relations even when not explicitly defined in SQLite)
            for c in cols_raw:
                cname = c['name']
                if cname in fk_map:
                    continue
                if cname == 'categoria_id':
                    fk_map[cname] = 'categorias.id'
                    all_fks.append((tname, cname, 'categorias', 'id'))
                elif cname == 'local_id':
                    fk_map[cname] = 'locais.id'
                    all_fks.append((tname, cname, 'locais', 'id'))
                elif cname == 'clube_id':
                    fk_map[cname] = 'clubes.id'
                    all_fks.append((tname, cname, 'clubes', 'id'))
                elif cname == 'livro_id':
                    fk_map[cname] = 'livros.id'
                    all_fks.append((tname, cname, 'livros', 'id'))
                elif cname == 'sessao_id':
                    fk_map[cname] = 'sessoes_leitura.id'
                    all_fks.append((tname, cname, 'sessoes_leitura', 'id'))
                elif cname == 'utilizador_id':
                    fk_map[cname] = 'utilizadores.id'
                    all_fks.append((tname, cname, 'utilizadores', 'id'))
                elif cname == 'evento_id':
                    fk_map[cname] = 'eventos.id'
                    all_fks.append((tname, cname, 'eventos', 'id'))
                elif cname == 'espetaculo_id':
                    target_table = 'espetaculos_tuna' if 'tuna' in tname else 'espetaculos'
                    fk_map[cname] = f'{target_table}.id'
                    all_fks.append((tname, cname, target_table, 'id'))
                elif cname == 'entidade_id':
                    fk_map[cname] = 'entidades_culturais.id'
                    all_fks.append((tname, cname, 'entidades_culturais', 'id'))


            columns = []
            for c in cols_raw:
                total_colunas += 1
                is_pk = bool(c['pk'])
                if is_pk:
                    total_pks += 1

                col_name = c['name']
                if col_name == 'id':
                    display_name = get_specific_id_name(tname)
                elif col_name.endswith('_id'):
                    ref_table = col_name[:-3]
                    if ref_table == 'categoria':
                        display_name = 'id_categoria'
                    elif ref_table == 'local':
                        display_name = 'id_local'
                    elif ref_table == 'clube':
                        display_name = 'id_clube'
                    elif ref_table == 'livro':
                        display_name = 'id_livro'
                    elif ref_table == 'sessao':
                        display_name = 'id_sessao_leitura'
                    elif ref_table == 'utilizador':
                        display_name = 'id_utilizador'
                    elif ref_table == 'evento':
                        display_name = 'id_evento'
                    elif ref_table == 'espetaculo':
                        display_name = 'id_espetaculo_tuna' if 'tuna' in tname else 'id_espetaculo'
                    elif ref_table == 'entidade':
                        display_name = 'id_entidade_cultural'
                    else:
                        display_name = f'id_{ref_table}'
                else:
                    display_name = col_name

                fk_val = fk_map.get(c['name'], None)
                if fk_val:
                    target_table, target_col = fk_val.split('.')
                    if target_col == 'id':
                        fk_val = f"{target_table}.{get_specific_id_name(target_table)}"

                columns.append({
                    'name': display_name,
                    'type': c['type'] or 'TEXT',
                    'pk': is_pk,
                    'fk': fk_val
                })

            tabelas.append({
                'name': tname,
                'columns': columns,
                'color': mod['color'],
                'icon': mod['icon'],
                'group': mod['group']
            })

    # 2. Gerar código Mermaid
    mermaid_lines = ['erDiagram', '']

    # Agrupar tabelas por módulo
    groups_order = ['Núcleo', 'Clubes', 'Leitura', 'Teatro', 'Tuna', 'Eventos', 'Outros']
    for grp in groups_order:
        grp_tables = [t for t in tabelas if t['group'] == grp]
        if not grp_tables:
            continue
        mermaid_lines.append(f'  %% ─── {grp.upper()} ───')
        for t in grp_tables:
            mermaid_lines.append(f'  {t["name"]} {{')
            for col in t['columns']:
                col_type = col['type'].split('(')[0].strip().lower()
                type_map = {
                    'integer': 'int', 'int': 'int',
                    'text': 'text', 'varchar': 'text',
                    'date': 'date', 'datetime': 'datetime', 'timestamp': 'datetime',
                    'time': 'time',
                    'real': 'float', 'decimal': 'float',
                    '': 'text'
                }
                mtype = type_map.get(col_type, 'text')
                # Mermaid ERD allows only ONE key constraint per column
                flags = ''
                if col['pk'] and col['fk']:
                    flags = ' FK'  # FK takes priority in junction tables
                elif col['pk']:
                    flags = ' PK'
                elif col['fk']:
                    flags = ' FK'
                mermaid_lines.append(f'    {mtype} {col["name"]}{flags}')
            mermaid_lines.append('  }')
        mermaid_lines.append('')

    # Relações
    mermaid_lines.append('  %% ═══ RELAÇÕES ═══')
    seen_rels = set()
    # Relações explícitas via FK
    for (from_t, from_c, to_t, to_c) in all_fks:
        rel_key = f'{to_t}-{from_t}'
        if rel_key not in seen_rels:
            seen_rels.add(rel_key)
            label = "1 para *"
            mermaid_lines.append(f'  {to_t} ||--o{{ {from_t} : "{label}"')

    mermaid_code = '\n'.join(mermaid_lines)

    return render_template('backoffice/esquema_bd.html',
                           tabelas=tabelas,
                           total_colunas=total_colunas,
                           total_fks=len(all_fks),
                           total_pks=total_pks,
                           db_version=db_version,
                           mermaid_code=mermaid_code)


@backoffice_bp.route('/atualizar-versao-bd', methods=['POST'])
@role_required('admin')
def atualizar_versao_bd():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("PRAGMA user_version")
            res = cursor.fetchone()
            current = res[0] if isinstance(res, tuple) else res['user_version']
            new_version = current + 1
            cursor.execute(f"PRAGMA user_version = {int(new_version)}")
        db.commit()
        flash(f"Esquema e versão da Base de Dados sincronizados com sucesso para a Versão v1.0.{new_version}!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Erro ao sincronizar versão da Base de Dados: {e}", "danger")
    return redirect(url_for('backoffice.esquema_bd'))


@backoffice_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """Permite a qualquer administrador editar os seus próprios dados de conta e configurar 2FA."""
    user_id = session.get('admin_id')
    utilizador = Utilizador.get_by_id(user_id)
    if not utilizador:
        flash('Utilizador não encontrado.', 'error')
        return redirect(url_for('backoffice.dashboard'))

    import pyotp
    erros = []
    
    # Recarregar do banco de dados para garantir os campos mfa
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT mfa_secret, mfa_ativo FROM utilizadores WHERE id = ?", (user_id,))
        mfa_data = cursor.fetchone()
        
    mfa_ativo = mfa_data['mfa_ativo'] if mfa_data else 0
    mfa_secret = mfa_data['mfa_secret'] if mfa_data else None

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not nome or not email:
            erros.append('Nome e E-mail são campos obrigatórios.')

        if password:
            from app.utils.security import avaliar_password
            classificacao, pontuacao, problemas, contem_padrao_fraco, e_proibida = avaliar_password(password)
            if classificacao == 'Fraca':
                erros.extend(problemas)
            else:
                # Prevenir reutilização de passwords
                db = get_db()
                with db.cursor() as cursor:
                    cursor.execute("SELECT password FROM utilizadores WHERE id = ?", (user_id,))
                    res = cursor.fetchone()
                    current_hash = res['password'] if res else None
                
                if current_hash and Utilizador.verificar_password(password, current_hash):
                    erros.append("A nova password não pode ser igual à password atual.")
                else:
                    # Comparar com histórico (últimas 3)
                    historico = Utilizador.obter_historico_passwords(user_id)
                    for h_hash in historico:
                        if Utilizador.verificar_password(password, h_hash):
                            erros.append("Não pode reutilizar uma password recentemente utilizada (histórico de passwords).")
                            break

        if not erros:
            dados = {
                'nome': nome,
                'username': utilizador['username'],
                'email': email,
                'role': utilizador['role'],
                'clube_id': utilizador.get('clube_id')
            }
            if password:
                dados['password'] = password

            if Utilizador.editar(user_id, dados):
                session['admin_nome'] = nome
                flash('Perfil atualizado com sucesso!', 'success')
                return redirect(url_for('backoffice.editar_perfil'))
            else:
                erros.append('Erro ao atualizar o perfil. E-mail ou utilizador já existente.')

    # Geração do segredo temporário para ativação de 2FA
    temp_secret = session.get('temp_mfa_secret')
    if not temp_secret:
        temp_secret = pyotp.random_base32()
        session['temp_mfa_secret'] = temp_secret

    otp_uri = pyotp.totp.TOTP(temp_secret).provisioning_uri(
        name=utilizador['email'],
        issuer_name="Lab Cultural ISPGAYA"
    )
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={otp_uri}"

    return render_template('backoffice/utilizadores/perfil.html',
                           utilizador=utilizador,
                           mfa_ativo=mfa_ativo,
                           temp_secret=temp_secret,
                           qr_code_url=qr_code_url,
                           erros=erros)


@backoffice_bp.route('/perfil/ativar-2fa', methods=['POST'])
@login_required
def confirmar_ativar_2fa():
    """Valida o código TOTP enviado pelo utilizador e ativa o 2FA."""
    user_id = session.get('admin_id')
    secret = session.get('temp_mfa_secret')
    code = request.form.get('code', '').strip()

    if not secret or not code:
        flash('Sessão de ativação 2FA inválida.', 'error')
        return redirect(url_for('backoffice.editar_perfil'))

    import pyotp
    totp = pyotp.TOTP(secret)
    if totp.verify(code, valid_window=1):
        if Utilizador.ativar_mfa(user_id, secret):
            session.pop('temp_mfa_secret', None)
            flash('Autenticação multifator (2FA) com Google Authenticator ativada com sucesso!', 'success')
        else:
            flash('Erro ao guardar configurações de MFA na Base de Dados.', 'error')
    else:
        flash('Código inválido ou expirado. Certifique-se de que a hora do telemóvel está sincronizada.', 'error')

    return redirect(url_for('backoffice.editar_perfil'))


@backoffice_bp.route('/perfil/desativar-2fa', methods=['POST'])
@login_required
def confirmar_desativar_2fa():
    """Desativa o 2FA na conta do utilizador."""
    user_id = session.get('admin_id')
    if Utilizador.desativar_mfa(user_id):
        flash('Autenticação de Dois Fatores (2FA) desativada.', 'info')
    else:
        flash('Erro ao desativar a autenticação multifator.', 'error')
    return redirect(url_for('backoffice.editar_perfil'))
