import sqlite3
import os

# Caminho para a base de dados SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'lab_cultural_flask', 'lab_cultural.db')

def create_tables(conn):
    cursor = conn.cursor()
    
    # Categorias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        icone TEXT DEFAULT '?',
        cor TEXT DEFAULT '#2563eb',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Locais
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        morada TEXT,
        cidade TEXT DEFAULT 'Vila Nova de Gaia',
        capacidade INTEGER,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Clubes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clubes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        descricao TEXT,
        icone TEXT DEFAULT '?',
        cor TEXT DEFAULT '#2563eb',
        local_id INTEGER,
        horario TEXT,
        imagem TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (local_id) REFERENCES locais (id) ON DELETE SET NULL
    )
    """)
    
    # Entidades Culturais
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entidades_culturais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        bio TEXT,
        tipo TEXT NOT NULL, -- enum('Autor','Ator','Encenador','Musico','Palestrante')
        imagem TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Espetaculos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS espetaculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        categoria_id INTEGER,
        tipo TEXT NOT NULL DEFAULT 'espetaculo', -- enum('espetaculo','ensaio','workshop')
        descricao TEXT,
        data_evento DATE NOT NULL,
        hora TIME,
        imagem TEXT,
        entrada TEXT NOT NULL DEFAULT 'gratuita', -- enum('gratuita','pago','convite')
        preco DECIMAL(6,2),
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duracao TEXT,
        classificacao_etaria TEXT,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        limite_filas INTEGER DEFAULT 8,
        data_publicacao DATETIME,
        FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL
    )
    """)
    
    # Eventos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eventos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        data_evento DATE NOT NULL,
        hora TIME,
        local_id INTEGER,
        imagem TEXT,
        link_externo TEXT,
        link_bilheteira TEXT,
        categoria_id INTEGER,
        tipo TEXT NOT NULL DEFAULT 'interno', -- enum('interno','externo')
        destaque INTEGER NOT NULL DEFAULT 0,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_publicacao DATETIME,
        tipo_ingresso TEXT DEFAULT 'gratis', -- enum('gratis','pago')
        preco DECIMAL(10,2) DEFAULT 0.00,
        limite_bilhetes INTEGER,
        FOREIGN KEY (local_id) REFERENCES locais (id) ON DELETE SET NULL,
        FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL
    )
    """)
    
    # Galeria Teatro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS galeria_teatro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        imagem TEXT NOT NULL,
        legenda TEXT,
        ordem INTEGER DEFAULT 0,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        espetaculo_id INTEGER,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (espetaculo_id) REFERENCES espetaculos (id) ON DELETE CASCADE
    )
    """)
    
    # Inscricoes Eventos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inscricoes_eventos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evento_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        codigo TEXT NOT NULL,
        valor_pago DECIMAL(8,2) DEFAULT 0.00,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (evento_id) REFERENCES eventos (id) ON DELETE CASCADE
    )
    """)
    
    # Inscricoes Leitura
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inscricoes_leitura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        utilizador_id INTEGER,
        sessao_id INTEGER,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        nome TEXT,
        email TEXT,
        estado TEXT DEFAULT 'Pendente', -- enum('Pendente','Aceite','Recusado')
        FOREIGN KEY (sessao_id) REFERENCES sessoes_leitura (id) ON DELETE CASCADE,
        FOREIGN KEY (utilizador_id) REFERENCES utilizadores (id) ON DELETE CASCADE
    )
    """)
    
    # Inscricoes Teatro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inscricoes_teatro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        espetaculo_id INTEGER,
        nome_aluno TEXT,
        email_aluno TEXT,
        codigo_inscricao TEXT UNIQUE,
        data_inscricao DATETIME DEFAULT CURRENT_TIMESTAMP,
        lugares TEXT,
        FOREIGN KEY (espetaculo_id) REFERENCES espetaculos (id)
    )
    """)
    
    # Livros
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS livros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        autor TEXT,
        categoria_id INTEGER,
        sinopse TEXT,
        imagem TEXT,
        ano INTEGER,
        genero TEXT,
        destaque INTEGER NOT NULL DEFAULT 0,
        mes_selecao TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        url_biblioteca TEXT,
        esta_disponivel INTEGER DEFAULT 1,
        FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL
    )
    """)
    
    # Membros Leitura
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membros_leitura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        estado TEXT DEFAULT 'Pendente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Membros Teatro
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membros_teatro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado TEXT DEFAULT 'Pendente'
    )
    """)
    
    # Noticias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        conteudo TEXT NOT NULL,
        resumo TEXT,
        imagem TEXT,
        categoria_id INTEGER,
        destaque INTEGER NOT NULL DEFAULT 0,
        ativo INTEGER NOT NULL DEFAULT 1,
        publicado_em DATE DEFAULT CURRENT_DATE,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL
    )
    """)
    
    # Requisicoes Livros
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requisicoes_livros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        livro_id INTEGER,
        nome_aluno TEXT,
        email_aluno TEXT,
        codigo_requisicao TEXT UNIQUE,
        data_requisicao DATETIME DEFAULT CURRENT_TIMESTAMP,
        estado TEXT DEFAULT 'Pendente',
        FOREIGN KEY (livro_id) REFERENCES livros (id)
    )
    """)
    
    # Sessoes Leitura
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessoes_leitura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        livro_id INTEGER,
        clube_id INTEGER,
        data_sessao DATE NOT NULL,
        hora TIME DEFAULT '18:30:00',
        local_id INTEGER,
        tema TEXT,
        descricao TEXT,
        vagas INTEGER,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (livro_id) REFERENCES livros (id) ON DELETE SET NULL,
        FOREIGN KEY (local_id) REFERENCES locais (id) ON DELETE SET NULL,
        FOREIGN KEY (clube_id) REFERENCES clubes (id) ON DELETE CASCADE
    )
    """)
    
    # Utilizadores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilizadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        nome TEXT NOT NULL,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        role TEXT NOT NULL DEFAULT 'admin',
        clube_id INTEGER,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (clube_id) REFERENCES clubes (id) ON DELETE SET NULL
    )
    """)
    
    # Espetaculo Equipa (N-N)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS espetaculo_equipa (
        espetaculo_id INTEGER NOT NULL,
        entidade_id INTEGER NOT NULL,
        funcao TEXT DEFAULT 'Ator',
        PRIMARY KEY (espetaculo_id, entidade_id),
        FOREIGN KEY (espetaculo_id) REFERENCES espetaculos (id) ON DELETE CASCADE,
        FOREIGN KEY (entidade_id) REFERENCES entidades_culturais (id) ON DELETE CASCADE
    )
    """)
    
    # Livro Autores (N-N)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS livro_autores (
        livro_id INTEGER NOT NULL,
        entidade_id INTEGER NOT NULL,
        PRIMARY KEY (livro_id, entidade_id),
        FOREIGN KEY (livro_id) REFERENCES livros (id) ON DELETE CASCADE,
        FOREIGN KEY (entidade_id) REFERENCES entidades_culturais (id) ON DELETE CASCADE
    )
    """)

    conn.commit()

def populate_initial_data(conn):
    cursor = conn.cursor()
    
    # Categorias
    categorias = [
        (1, 'Teatro', '🎭', '#7c3aed'),
        (2, 'Literatura', '📚', '#2563eb'),
        (3, 'Música', '🎵', '#db2777'),
        (4, 'Exposição', '🖼️', '#d97706'),
        (5, 'Cinema', '🎬', '#059669'),
        (6, 'Dança', '💃', '#dc2626'),
        (7, 'Conferência', '🎤', '#0891b2')
    ]
    cursor.executemany("INSERT OR IGNORE INTO categorias (id, nome, icone, cor) VALUES (?, ?, ?, ?)", categorias)
    
    # Utilizadores (Password é a mesma do dump: admin / Joa / marco)
    utilizadores = [
        (2, 'admin', '$2b$12$B7bXBEH2DzlLnUmC516vDerhFW0G5Q4x2OptuqcmALSanuec8MSnO', 'admin@gmail.com', 'Administrador', 'admin'),
        (3, 'Joao', '$2b$12$ssySepPiievHmNoSgON5Ne6d1nHgnkrhbrElXP3LTgVe78t3kJBn.', 'Joao@joao.pt', 'Joao', 'teatro'),
        (4, 'marco', '$2b$12$R5WdVhj27bXvXZbptF9PFu9PequbBBEGnHNfcWOITLsbSWxN4FJJ2', 'marco@gmail.com', 'marco', 'leitura')
    ]
    cursor.executemany("INSERT OR IGNORE INTO utilizadores (id, username, password, email, nome, role) VALUES (?, ?, ?, ?, ?, ?)", utilizadores)
    
    # Locais
    locais = [
        (1, 'Porto', None, 'Porto', None),
        (2, 'ISPGAYA / Vila Nova de Gaia', None, 'Vila Nova de Gaia', None),
        (3, 'Espinho', None, 'Espinho', None)
    ]
    cursor.executemany("INSERT OR IGNORE INTO locais (id, nome, morada, cidade, capacidade) VALUES (?, ?, ?, ?, ?)", locais)

    conn.commit()

if __name__ == "__main__":
    print(f"A criar base de dados em: {DB_PATH}")
    connection = sqlite3.connect(DB_PATH)
    create_tables(connection)
    populate_initial_data(connection)
    connection.close()
    print("Sucesso!")
