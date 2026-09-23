# 🗄️ Modelo de Dados — Diagrama de Entidade-Relação (ERD)

Este documento contém a representação gráfica do modelo de base de dados relacional da plataforma **LabCultural**. 

O diagrama está construído utilizando a sintaxe **Mermaid**. Pode ser visualizado diretamente no GitHub ou em qualquer visualizador de Markdown compatível com Mermaid.

---

## 📊 Diagrama ERD

```mermaid
erDiagram
    CATEGORIAS {
        integer id PK
        text nome UNIQUE
        text icone
        text cor
        timestamp criado_em
        timestamp atualizado_em
    }

    LOCAIS {
        integer id PK
        text nome
        text morada
        text cidade
        integer capacidade
        timestamp criado_em
        timestamp atualizado_em
    }

    CLUBES {
        integer id PK
        text nome
        text slug UNIQUE
        text descricao
        text icone
        text cor
        integer local_id FK
        text horario
        text imagem
        integer ativo
        timestamp criado_em
        timestamp atualizado_em
    }

    ENTIDADES_CULTURAIS {
        integer id PK
        text nome
        text bio
        text tipo
        text imagem
        timestamp criado_em
        timestamp atualizado_em
    }

    ESPETACULOS {
        integer id PK
        text titulo
        integer categoria_id FK
        text tipo
        text descricao
        date data_evento
        time hora
        text imagem
        text entrada
        decimal preco
        integer ativo
        integer limite_filas
        datetime data_publicacao
        timestamp criado_em
        timestamp atualizado_em
    }

    EVENTOS {
        integer id PK
        text titulo
        text descricao
        date data_evento
        time hora
        integer local_id FK
        text imagem
        text link_externo
        text link_bilheteira
        integer categoria_id FK
        text tipo
        integer destaque
        integer ativo
        text tipo_ingresso
        decimal preco
        integer limite_bilhetes
        datetime data_publicacao
        timestamp criado_em
        timestamp atualizado_em
    }

    GALERIA_TEATRO {
        integer id PK
        text titulo
        text imagem
        text legenda
        integer ordem
        integer ativo
        integer espetaculo_id FK
        timestamp criado_em
        timestamp atualizado_em
    }

    INSCRICOES_EVENTOS {
        integer id PK
        integer evento_id FK
        text nome
        text email
        text codigo
        decimal valor_pago
        timestamp criado_em
    }

    INSCRICOES_LEITURA {
        integer id PK
        integer utilizador_id FK
        integer sessao_id FK
        text nome
        text email
        text estado
        timestamp criado_em
    }

    INSCRICOES_TEATRO {
        integer id PK
        integer espetaculo_id FK
        text nome_aluno
        text email_aluno
        text codigo_inscricao UNIQUE
        datetime data_inscricao
        text lugares
    }

    LIVROS {
        integer id PK
        text titulo
        text autor
        integer categoria_id FK
        text sinopse
        text imagem
        integer ano
        text genero
        integer destaque
        text mes_selecao
        text url_biblioteca
        integer esta_disponivel
        timestamp criado_em
        timestamp atualizado_em
    }

    REQUISICOES_LIVROS {
        integer id PK
        integer livro_id FK
        text nome_aluno
        text email_aluno
        text codigo_requisicao UNIQUE
        datetime data_requisicao
        text estado
    }

    SESSOES_LEITURA {
        integer id PK
        integer livro_id FK
        integer clube_id FK
        date data_sessao
        time hora
        integer local_id FK
        text tema
        text descricao
        integer vagas
        integer ativo
        timestamp criado_em
        timestamp atualizado_em
    }

    UTILIZADORES {
        integer id PK
        text username UNIQUE
        text password
        text email UNIQUE
        text nome
        integer ativo
        text role
        integer clube_id FK
        timestamp criado_em
        timestamp atualizado_em
    }

    NOTICIAS {
        integer id PK
        text titulo
        text conteudo
        text resumo
        text imagem
        integer categoria_id FK
        integer destaque
        integer ativo
        date publicado_em
        timestamp criado_em
        timestamp atualizado_em
    }

    ESPETACULO_EQUIPA {
        integer espetaculo_id PK_FK
        integer entidade_id PK_FK
        text funcao
    }

    LIVRO_AUTORES {
        integer livro_id PK_FK
        integer entidade_id PK_FK
    }

    %% Tabelas da Tuna Académica
    ESPETACULOS_TUNA {
        integer id PK
        text titulo
        text descricao
        text tipo
        date data_evento
        time hora
        text entrada
        decimal preco
        text imagem
        text duracao
        integer limite_filas
        datetime data_publicacao
        integer destaque
        integer ativo
    }

    GALERIA_TUNA {
        integer id PK
        integer espetaculo_id FK
        text titulo
        text imagem
        integer ordem
        integer ativo
        timestamp criado_em
    }

    MEMBROS_TUNA {
        integer id PK
        text nome
        text email
        text estado
        timestamp criado_em
    }

    MEMBROS_LEITURA {
        integer id PK
        text nome
        text email
        text estado
        timestamp criado_em
    }

    MEMBROS_TEATRO {
        integer id PK
        text nome
        text email
        text estado
        timestamp criado_em
    }

    MENSAGENS_CONTACTO {
        integer id PK
        text nome
        text email
        text mensagem
        timestamp criado_em
    }

    %% Relações e Cardinalidades
    LOCAIS ||--o{ CLUBES : "local_id"
    LOCAIS ||--o{ EVENTOS : "local_id"
    LOCAIS ||--o{ SESSOES_LEITURA : "local_id"

    CATEGORIAS ||--o{ ESPETACULOS : "categoria_id"
    CATEGORIAS ||--o{ EVENTOS : "categoria_id"
    CATEGORIAS ||--o{ LIVROS : "categoria_id"
    CATEGORIAS ||--o{ NOTICIAS : "categoria_id"

    CLUBES ||--o{ SESSOES_LEITURA : "clube_id"
    CLUBES ||--o{ UTILIZADORES : "clube_id"

    ESPETACULOS ||--o{ GALERIA_TEATRO : "espetaculo_id"
    ESPETACULOS ||--o{ INSCRICOES_TEATRO : "espetaculo_id"

    EVENTOS ||--o{ INSCRICOES_EVENTOS : "evento_id"

    LIVROS ||--o{ REQUISICOES_LIVROS : "livro_id"
    LIVROS ||--o{ SESSOES_LEITURA : "livro_id"

    UTILIZADORES ||--o{ INSCRICOES_LEITURA : "utilizador_id"
    SESSOES_LEITURA ||--o{ INSCRICOES_LEITURA : "sessao_id"

    %% Relações N:M (Associativas)
    ESPETACULOS ||--o{ ESPETACULO_EQUIPA : "espetaculo_id"
    ENTIDADES_CULTURAIS ||--o{ ESPETACULO_EQUIPA : "entidade_id"

    LIVROS ||--o{ LIVRO_AUTORES : "livro_id"
    ENTIDADES_CULTURAIS ||--o{ LIVRO_AUTORES : "entidade_id"

    %% Relações da Tuna
    ESPETACULOS_TUNA ||--o{ GALERIA_TUNA : "espetaculo_id"
```

---

## 📌 Como incluir no Word:

1. **Opção Recomendada (Exportar Imagem)**:
   - Abra este ficheiro no VS Code (ou use um renderizador Mermaid como [mermaid.live](https://mermaid.live)).
   - Copie o código acima e cole no editor online.
   - Descarregue o diagrama como uma imagem de alta resolução (PNG ou SVG).
   - Insira a imagem no Word na **Secção 4.1 (Modelo Entidade-Relação)** ou no **Anexo C**.
   - Substitua o texto "Figura X" por **Figura 4** (ou o número correspondente).

2. **Opção Alternativa (Inserir Legenda no Word)**:
   - Legenda sugerida no Word: 
     > *Figura 4: Diagrama Entidade-Relação completo da plataforma LabCultural contendo as tabelas do Front-office, Back-office, Clubes e Tuna Académica.*
