# Relatório de Análise do Website — Laboratório Cultural ISPGAYA

Este documento apresenta uma análise detalhada da arquitetura, estrutura de dados, interface e aspetos estéticos e funcionais do website do **Laboratório Cultural do ISPGAYA**. Também são destacadas as correções de bugs efetuadas durante a análise.

---

## 1. Arquitetura da Aplicação

A aplicação foi desenvolvida utilizando uma arquitetura moderna e robusta para a Web:

- **Backend**: Desenvolvido em **Flask (Python)** com uma estrutura modular dividida em Blueprints (`frontoffice`, `backoffice`, `auth`, `api`).
- **Base de Dados**: **SQLite** (com ficheiro armazenado em `app/database/lab_cultural.db`), proporcionando um acesso rápido e estruturado aos dados.
- **Frontend**: Combina **Tailwind CSS** (via CDN com configurações personalizadas de marca), **FontAwesome** para ícones e **Vanilla JavaScript** para interações dinâmicas (AJAX, modais, autocomplete e mapa de lugares do teatro).
- **Segurança**: Autenticação de utilizadores gerida através de sessões seguras do Flask com palavras-passe encriptadas via `werkzeug.security`.

---

## 2. Estrutura do Base de Dados

A base de dados SQLite (`lab_cultural.db`) contém tabelas bem definidas que gerem a totalidade dos dados da aplicação:

1. **`utilizadores`**: Armazena utilizadores do backoffice (com campos como `username`, `password_hash`, `email`, `role` e `ativo`).
2. **`categorias`**: Categorias de eventos e notícias (ex: Literatura, Música, Teatro, Geral).
3. **`eventos`**: Informações sobre eventos gerais (título, descrição, data, local, limite de bilhetes, imagem).
4. **`inscricoes_eventos`**: Registos de inscrições em eventos gerais, associados ao email institucional do utilizador (`@ispgaya.pt`).
5. **`livros`**: Catálogo da biblioteca com metadados detalhados (autor, ano, género, ISBN, exemplar único e estado de disponibilidade).
6. **`requisicoes_livros`**: Registo de empréstimo de livros contendo estados de requisição (`pendente`, `aprovado`, `devolvido`, `rejeitado`).
7. **`clubes`**: Registo dos clubes existentes (Teatro, Tuna Académica, etc.).
8. **`espetaculos`**: Agenda de produções teatrais com parametrização de lotação (filas e colunas).
9. **`inscricoes_teatro`**: Reservas de bilhetes para o teatro com escolha do lugar no mapa interativo da sala.
10. **`espetaculos_tuna`**: Eventos e atuações da Tuna Académica.
11. **`noticias`**: Conteúdo informativo da secção de notícias da instituição.
12. **`galeria_fotos`**: Fotografias organizadas por grupos e clubes para o registo histórico visual.

---

## 3. Análise Funcional e Estética

O design da plataforma foi estruturado para refletir a identidade visual corporativa do **ISPGAYA**:

- **Paleta de Cores**: Uso do laranja característico do ISPGAYA (`#f37021`) como tom de destaque, contrastado com brancos limpos, cinzas estruturais (`#1a1a1a`) e tipografias contrastantes.
- **Tipografia**: Associação de fontes premium através do Google Fonts:
  - **Inter**: Para corpos de texto, formulários e botões, maximizando a legibilidade.
  - **Libre Baskerville**: Fonte Serif utilizada em títulos principais (`h1`, `h2`), conferindo um caráter editorial e cultural de prestígio.
- **Micro-animações**: Hover em botões e imagens com transições suaves (como efeitos de escala e remoção de filtros grayscale na galeria), que enriquecem a experiência do utilizador.
- **Interatividade Assíncrona**: Utilização de `fetch` no JavaScript para realizar filtros de pesquisa em tempo real, paginação rápida sem recarregamento de página e autocomplete inteligente.

---

## 4. Análise de Secções (Front-office & Back-office)

### Front-office
- **Página Inicial (Index)**: Apresentação moderna com os grandes destaques do Laboratório, links rápidos para as atividades e as secções de destaque.
- **Clube de Teatro**: Área dedicada contendo informações de ensaios, agenda de espetáculos e reservas integradas com um mapa de lugares interativo (onde os utilizadores escolhem a fila e a cadeira).
- **Tuna Académica**: Divulgação da atividade da tuna, elementos e galeria de fotos.
- **Biblioteca**: Catálogo interativo de livros com pesquisa e opção para requisição direta através de e-mail institucional.
- **Eventos & Notícias**: Listagem cronológica e filtragem dinâmica por categoria e data.

### Back-office
- **Dashboard**: Vista com métricas operacionais (total de eventos, livros, utilizadores e inscrições por mês) representadas em gráficos e listas interativas.
- **Gestão de Conteúdos**: Painéis de CRUD completos para Eventos, Livros, Notícias, Clubes, Espetáculos de Teatro e Utilizadores do painel.
- **Aprovação de Requisições**: Interface para aprovar ou rejeitar requisições de livros da biblioteca e gerir o fluxo de devoluções.

---

## 5. Correções de Bugs Efetuadas

Durante a análise exploratória e técnica do site, foram identificados e corrigidos três problemas específicos:

### A. Bug de Contexto na Galeria da Tuna Académica
- **Problema**: A galeria fotográfica da Tuna Académica (`/lab-cultural/tuna/galeria`) utilizava o mesmo template estático do Clube de Teatro (`galeria_teatro.html`). Consequentemente, o cabeçalho, a descrição, as migalhas de pão (breadcrumbs) e o botão de regresso faziam referência incorreta ao "Clube de Teatro" e ligavam à rota errada.
- **Resolução**: 
  - Alterou-se o controlador backend `frontoffice.py` para passar o parâmetro `clube_tipo` com os valores `'teatro'` ou `'tuna'`.
  - Atualizou-se o template `galeria_teatro.html` para renderizar dinamicamente os títulos, descrições, breadcrumbs e links de retorno conforme o tipo de clube selecionado.
  - Ajustou-se o JavaScript de autocomplete para ignorar sugestões de peças teatrais quando se visualiza a galeria da Tuna Académica, mantendo a pesquisa e filtros dinâmicos de fotos a funcionar de forma independente.

### B. Erros Gramaticais na Listagem de Notícias
- **Problema**: Havia pequenos desvios gramaticais de português na página de notícias (`noticias.html`):
  - Na descrição inicial lia-se: *"Fica a conhecer **os** noticias..."* (em vez de *"as notícias"*).
  - No texto de fallback das notícias lia-se: *"Descobre mais sobre **este** noticia..."* (em vez de *"esta notícia"*).
- **Resolução**: Ambos os trechos de texto foram revistos e corrigidos para garantir uma escrita correta e cuidada na interface.

---

## 6. Oportunidades de Melhoria Futuras
1. **Páginas de Erro Personalizadas**: Criar templates personalizados para erros `404` (Não Encontrado) e `500` (Erro do Servidor) que combinem com a estética do site.
2. **Histórico do Aluno**: Adicionar uma área no frontoffice onde o aluno possa introduzir o seu email institucional e visualizar todas as suas requisições de livros ativas e inscrições em eventos ou teatro.
