# 🎨 Protótipos e Wireframes (Momento 1)

> **Instruções para o Word**: Copie o texto abaixo e cole no seu relatório na secção dedicada ao Planeamento Visual / Momento 1 (antes do Capítulo 6). Insira as respetivas figuras da pasta `relatorio/wireframes/` nos locais indicados.

---

## 2.X Planeamento Visual e Protótipos (Wireframes)

Na fase inicial do projeto (Momento 1), correspondente à análise e planeamento, procedeu-se à elaboração de esboços de interface de baixa fidelidade (*wireframes*). O objetivo deste processo foi definir a arquitetura de informação, a hierarquia visual dos componentes e os fluxos de navegação básicos sem a influência de cores, tipografia final ou elementos de marca, assegurando um foco estrito na usabilidade e experiência do utilizador (UX).

A modelação das interfaces focou-se nas três áreas principais e de maior complexidade interativa do website público (Front-office): a Homepage do Laboratório, a Bilheteira do Teatro com o Mapa de Sala, e o Catálogo/Requisição de Livros da Biblioteca.

### 2.X.1 Homepage do Laboratório Cultural
O wireframe da Homepage estabelece a grelha estrutural e os blocos de conteúdos destinados à promoção cultural da instituição. 

*   **Zonas Principais**:
    *   **Cabeçalho Geral**: Logótipo institucional alinhado à esquerda e menu de navegação horizontal à direita, garantindo consistência com o site oficial do ISPGAYA.
    *   **Secção Hero**: Área de grande impacto visual com título de destaque, descrição da missão do Laboratório Cultural e botão de chamada à ação (*Call to Action* - CTA).
    *   **Grelha de Clubes**: Apresentação dos três clubes (Leitura, Teatro e Tuna) em formato de blocos de igual dimensão, facilitando a navegação direta do utilizador.
    *   **Destaques de Eventos**: Carrossel ou grelha de três colunas para os próximos eventos em destaque, indicando título, data, local e botão para ver detalhes.
    *   **Rodapé**: Links úteis, contactos institucionais e o *widget* de consentimento de cookies.

*(Inserir Figura: `wireframe_homepage.png` — Legenda: Figura X: Wireframe de baixa fidelidade da Homepage do Laboratório Cultural)*

### 2.X.2 Módulo de Teatro: Bilheteira e Mapa de Lugares
O wireframe da página de reservas do Clube de Teatro representa o componente mais interativo do projeto, detalhando a interface de reserva de assentos.

*   **Zonas Principais**:
    *   **Cabeçalho da Peça**: Título do espetáculo, sinopse, duração, classificação etária e detalhes da sessão (data, hora e preço).
    *   **Representação do Palco**: Um bloco visual superior indicando a orientação do palco da sala.
    *   **Mapa de Lugares Bidimensional**: Grelha de assentos operáveis organizada por filas e colunas. Cada assento possui um estado visual mapeado: *Livre*, *Reservado* (desabilitado) e *Selecionado* (destaque interativo).
    *   **Painel Lateral de Sumário**: Exibe em tempo real o número de assentos selecionados, os identificadores de cada lugar (ex: Fila A - Lugar 4) e o valor total acumulado.
    *   **Formulário de Inscrição**: Campos obrigatórios para o Nome e o E-mail Institucional (`@ispgaya.pt`), acompanhados do botão de confirmação de reserva.

*(Inserir Figura: `wireframe_teatro.png` — Legenda: Figura X: Wireframe de baixa fidelidade do Mapa de Lugares Interativo do Clube de Teatro)*

### 2.X.3 Biblioteca: Catálogo Virtual e Empréstimos
O wireframe da Biblioteca documenta a interface de pesquisa, listagem e requisição de obras literárias.

*   **Zonas Principais**:
    *   **Barra de Pesquisa e Filtros**: Input de pesquisa de texto por título/autor e seletor dropdown para filtragem rápida por categorias de literatura.
    *   **Destaque do Livro do Mês**: Bloco de destaque com maior peso visual exibindo a capa, autor, ano e sinopse da obra selecionada para o mês corrente.
    *   **Grelha do Catálogo**: Disposição de livros em cards, contendo a capa do livro, título, autor e um indicador visual de estado (*Disponível* a verde ou *Indisponível* a vermelho).
    *   **Modal de Requisição**: Interface sobreposta (modal) que surge ao clicar em "Requisitar". Contém os dados da obra e solicita o preenchimento dos dados do aluno (Nome e E-mail institucional) para envio do pedido.

*(Inserir Figura: `wireframe_biblioteca.png` — Legenda: Figura X: Wireframe de baixa fidelidade do Catálogo de Livros e Sistema de Empréstimos)*
