from flask import Flask, g
import pymysql
import pymysql.cursors
import os
import random
from config import Config

# Imagens de leitura e teatro disponíveis nos multimedia_assets
LEITURA_IMAGES = [f'livro{i}.jpg' for i in range(1, 8)] + [f'livro_{i}.jpg' for i in range(1, 14)]
TEATRO_IMAGES = [
    'espetaculo_1.jpg', 'espetaculo_2.jpg', 'espetaculo_3.jpg', 'espetaculo_4.jpg', 
    'espetaculo_5.jpg', 'espetaculo_6.jpg', 'espetaculo_7.jpg',
    'espetaculo_8.jpg', 'espetaculo_9.jpg', 'espetaculo_10.jpg',
    'espetaculo_2_2.jpg', 'espetaculo_2_3.jpg', 'espetaculo_2_4.jpg', 'espetaculo_2_5.jpg',
    'espetaculo_3_1.jpg', 'espetaculo_3_2.jpg', 'espetaculo_3_3.jpg', 'espetaculo_3_4.jpg',
    'espetaculo_3_5.jpg', 'espetaculo_3_6.jpg', 'espetaculo_3_7.jpg'
]


import sqlite3
from datetime import datetime, date

# Registar conversores para garantir que datas em SQLite sejam lidas como objetos Python
def adapt_datetime(ts):
    return ts.isoformat()

def convert_datetime(s):
    try:
        return datetime.fromisoformat(s.decode())
    except:
        return s.decode()

sqlite3.register_converter("DATETIME", convert_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)
sqlite3.register_converter("DATE", lambda s: datetime.strptime(s.decode(), '%Y-%m-%d').date())

class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        # Converte placeholders de MySQL (%s) para SQLite (?)
        query = query.replace('%s', '?')
        # Converte funções comuns de MySQL para SQLite
        query = query.replace('NOW()', "datetime('now', 'localtime')")
        query = query.replace('CURDATE()', "date('now', 'localtime')")
        
        if params is None:
            return self.cursor.execute(query)
        return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()

class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, **kwargs):
        # Ignora argumentos como cursorclass do pymysql
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

def get_db():
    """Retorna a ligação à BD para o request atual."""
    if 'db' not in g:
        if Config.DB_TYPE == 'sqlite':
            # detect_types permite que o sqlite3 converta DATE e TIMESTAMP para objetos Python
            conn = sqlite3.connect(
                Config.SQLITE_DB, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Row factory que retorna um dicionário real para suportar .get()
            conn.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}
            g.db = SQLiteConnectionWrapper(conn)
        else:
            g.db = pymysql.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                port=Config.MYSQL_PORT,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
    return g.db


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # ── Função global Jinja2: imagem aleatória por tipo ──
    def random_image(tipo='leitura'):
        """Retorna o caminho relativo (para url_for static) de uma imagem
        aleatória da pasta leitura ou teatro dentro de static/img/.
        Permite repetição entre chamadas."""
        if tipo == 'teatro':
            img = random.choice(TEATRO_IMAGES)
            return f'img/teatro/{img}'
        else:
            img = random.choice(LEITURA_IMAGES)
            return f'img/leitura/{img}'

    app.jinja_env.globals['random_image'] = random_image

    @app.context_processor
    def inject_notificacoes():
        """Injeta contagens de notificações para o sidebar do Backoffice."""
        try:
            db = get_db()
            with db.cursor() as cursor:
                # Mensagens não lidas
                cursor.execute("SELECT COUNT(*) as total FROM mensagens_contacto WHERE lida = 0")
                msg_count = cursor.fetchone()['total']
                
                # Requisições pendentes
                cursor.execute("SELECT COUNT(*) as total FROM requisicoes_livros WHERE estado = 'Pendente'")
                req_count = cursor.fetchone()['total']
                
                # Membros de leitura pendentes
                cursor.execute("SELECT COUNT(*) as total FROM membros_leitura WHERE estado = 'Pendente'")
                membros_leitura_count = cursor.fetchone()['total']
                
                # Membros de teatro pendentes
                cursor.execute("SELECT COUNT(*) as total FROM membros_teatro WHERE estado = 'Pendente'")
                membros_teatro_count = cursor.fetchone()['total']
                
                # Membros de tuna pendentes
                cursor.execute("SELECT COUNT(*) as total FROM membros_tuna WHERE estado = 'Pendente'")
                membros_tuna_count = cursor.fetchone()['total']
                
                return {
                    'notificacoes_bo': {
                        'mensagens': msg_count,
                        'requisicoes': req_count,
                        'membros_leitura': membros_leitura_count,
                        'membros_teatro': membros_teatro_count,
                        'membros_tuna': membros_tuna_count,
                        'total': msg_count + req_count + membros_leitura_count + membros_teatro_count + membros_tuna_count
                    }
                }
        except:
            return {'notificacoes_bo': {'mensagens': 0, 'requisicoes': 0, 'membros_leitura': 0, 'membros_teatro': 0, 'membros_tuna': 0, 'total': 0}}

    @app.template_filter('zfill')
    def zfill_filter(s, width=2):
        return str(s).zfill(width)

    # Registar blueprints
    from app.controllers.frontoffice import frontoffice_bp
    from app.controllers.auth import auth_bp
    from app.controllers.backoffice import backoffice_bp
    from app.controllers.api import api_bp

    app.register_blueprint(frontoffice_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/admin')
    app.register_blueprint(backoffice_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
