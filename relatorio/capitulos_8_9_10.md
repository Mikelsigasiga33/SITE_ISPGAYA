8. SEGURANÇA

O presente capítulo documenta as medidas de segurança implementadas na plataforma LabCultural, abrangendo a prevenção de ataques comuns em aplicações web, a proteção de credenciais, a validação de dados e o controlo de sessões.


8.1 Prevenção de Cross-Site Scripting (XSS)

Os ataques de Cross-Site Scripting consistem na injeção de código malicioso (tipicamente JavaScript) em páginas web, com o objetivo de comprometer a sessão de outros utilizadores ou roubar informação sensível. Para prevenir este tipo de ataque, foram implementadas duas camadas de proteção complementares.

A primeira camada consiste na sanitização de inputs do lado do servidor. O módulo app/utils/security.py define a função sanitize(), que utiliza a função html.escape() da biblioteca padrão do Python para converter caracteres potencialmente perigosos (<, >, &, ", ') nas respetivas entidades HTML. Esta função é invocada em todos os controladores antes de qualquer operação de inserção ou atualização na base de dados:

    def sanitize(text):
        if text is None:
            return ''
        return html.escape(str(text).strip())

Para facilitar a sanitização de múltiplos campos em simultâneo, foi desenvolvida a função sanitizar_dict(), que recebe um dicionário e uma lista de campos a sanitizar, devolvendo um novo dicionário com os valores limpos:

    def sanitizar_dict(dados, campos):
        resultado = {}
        for campo in campos:
            resultado[campo] = sanitize(dados.get(campo, ''))
        return resultado

A segunda camada de proteção é proporcionada pelo motor de templates Jinja2, que aplica auto-escape a todas as variáveis inseridas nos templates HTML. Isto significa que qualquer valor proveniente da base de dados é automaticamente escapado antes de ser renderizado na página, impedindo a execução de scripts injetados.


8.2 Prevenção de SQL Injection

Os ataques de SQL Injection consistem na inserção de instruções SQL maliciosas através de campos de input, com o objetivo de manipular ou extrair dados da base de dados. Para prevenir este tipo de ataque, todas as queries SQL da plataforma utilizam parâmetros parametrizados (placeholders), em vez de concatenação direta de strings.

No código dos modelos, os valores fornecidos pelo utilizador são sempre passados como parâmetros separados da query:

    cursor.execute(
        "SELECT * FROM utilizadores WHERE username = %s AND ativo = 1",
        (username,)
    )

A camada de abstração SQLiteCursorWrapper traduz automaticamente os placeholders %s (sintaxe MySQL) para ? (sintaxe SQLite), mantendo a parametrização em ambos os motores de base de dados. Esta abordagem garante que os valores do utilizador são tratados exclusivamente como dados e nunca como código SQL.

Em nenhum ponto do código-fonte é utilizada concatenação direta de strings para construir queries SQL com valores provenientes do utilizador.


8.3 Hash de Passwords

As passwords dos utilizadores do backoffice são armazenadas na base de dados como hashes criptográficos gerados pelo algoritmo bcrypt, que é especificamente concebido para o armazenamento seguro de credenciais.

Na criação de um novo utilizador, a password é transformada num hash com salt gerado automaticamente:

    import bcrypt
    hashed = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

Na verificação durante o login, a password introduzida é comparada com o hash armazenado utilizando a função bcrypt.checkpw(), que implementa uma comparação em tempo constante para prevenir ataques de timing:

    bcrypt.checkpw(
        password.encode('utf-8'),
        hash_armazenado.encode('utf-8')
    )

O algoritmo bcrypt foi selecionado pelas seguintes razões: incorpora automaticamente um salt aleatório em cada hash, prevenindo ataques com rainbow tables; é intencionalmente lento (computacionalmente custoso), dificultando ataques de força bruta; e o fator de custo pode ser ajustado para acompanhar a evolução do hardware.


8.4 Validação de Inputs

A validação de dados é efetuada em duas camadas complementares: do lado do cliente (JavaScript) para feedback imediato ao utilizador, e do lado do servidor (Python) como barreira definitiva de segurança.

No lado do servidor, o módulo security.py disponibiliza as seguintes funções de validação:

A função validar_email() verifica se um endereço de e-mail segue o formato padrão (utilizador@dominio.tld) através de uma expressão regular.

A função validar_data() verifica se uma string de data segue o formato YYYY-MM-DD, tentando construir um objeto datetime e devolvendo False em caso de exceção.

A função validar_hora() verifica se uma string de hora segue o formato HH:MM, com lógica análoga.

A função validar_campos() recebe um dicionário de dados e uma lista de campos obrigatórios, devolvendo uma lista de erros para cada campo em falta ou vazio.

A função allowed_file() verifica se a extensão de um ficheiro carregado está incluída no conjunto de extensões permitidas (png, jpg, jpeg, gif, webp), prevenindo o upload de ficheiros potencialmente perigosos.

A configuração MAX_CONTENT_LENGTH = 5 * 1024 * 1024 no ficheiro config.py limita o tamanho máximo de uploads a 5 MB, prevenindo ataques de negação de serviço por exaustão de espaço em disco.


8.5 Avaliação de Robustez de Passwords

Para além do armazenamento seguro, o sistema implementa um mecanismo proativo de avaliação da qualidade das passwords definidas pelos administradores. A função avaliar_password() no módulo security.py analisa uma password segundo múltiplos critérios:

Lista negra de passwords proibidas. O sistema verifica se a password consta numa lista de passwords comuns frequentemente utilizadas em ataques de dicionário (123456, password, admin, qwerty, entre outras). Passwords presentes nesta lista são automaticamente classificadas como fracas, independentemente de outros critérios.

Deteção de padrões fracos. O sistema procura sequências e padrões previsíveis dentro da password (123, abcd, qwerty, admin, password). A presença destes padrões reduz a pontuação da password.

Critérios de complexidade. A pontuação da password é calculada com base nos seguintes critérios: comprimento (1 ponto para 8 ou mais caracteres, 2 pontos para 12 ou mais); presença de letras minúsculas (1 ponto); presença de letras maiúsculas (1 ponto); presença de números (1 ponto); e presença de símbolos ou caracteres especiais (1 ponto).

Classificação final. Com base na pontuação acumulada, a password é classificada como Fraca (pontuação até 2 ou comprimento inferior a 8), Média (pontuação 3 a 4), Forte (pontuação 5) ou Muito forte (pontuação 6).

Esta avaliação é disponibilizada em tempo real no formulário de criação e edição de utilizadores através do endpoint /api/v1/avaliar-password, proporcionando feedback visual instantâneo ao administrador com uma barra de progresso colorida e a lista de problemas identificados. O sistema impede a submissão de passwords classificadas como fracas.


8.6 Controlo de Sessões

As sessões do backoffice são geridas pelo mecanismo nativo do Flask, que armazena os dados da sessão num cookie assinado criptograficamente com a SECRET_KEY definida no ficheiro de configuração.

A assinatura do cookie garante que o seu conteúdo não pode ser alterado pelo cliente sem invalidar a assinatura. A SECRET_KEY é carregada preferencialmente a partir de uma variável de ambiente, garantindo que não é exposta no código-fonte em ambientes de produção.

No logout, a função session.clear() elimina todos os dados da sessão, invalidando imediatamente o acesso do utilizador ao backoffice. Todas as rotas protegidas verificam a presença da variável admin_logado na sessão antes de permitir o acesso, garantindo que utilizadores com sessões expiradas ou inválidas são redirecionados para a página de login.


8.7 Mapeamento de Vulnerabilidades (OWASP Top 10)

Para atestar o grau de segurança da plataforma, apresenta-se uma matriz de correspondência face aos riscos catalogados no OWASP Top 10, demonstrando de que forma as vulnerabilidades mais críticas foram acauteladas durante o desenvolvimento.

Risco OWASP Top 10 | Estratégia de Mitigação no LabCultural
--- | ---
A01:2021 – Broken Access Control | Verificação estrita nos decorators @login_required e @role_required aplicada a rotas de backoffice. Implementação de RBAC.
A02:2021 – Cryptographic Failures | Hashes de passwords armazenados com bcrypt. O sistema resiste a rainbow table attacks com salting nativo.
A03:2021 – Injection (inclui XSS) | Queries SQL parametrizadas (? e %s) extinguindo SQL Injection. Injeções de JS acauteladas via html.escape e Jinja2.
A04:2021 – Insecure Design | Longevidade dos códigos QR gerados para os tickets controlada via cronologias rígidas (expiração automática).
A07:2021 – Identification | O logout no backend executa uma limpeza irreversível (session.clear()), removendo a cache da sessão de imediato.
A08:2021 – Software Integrity | A aplicação controla o tamanho em bytes pelo MAX_CONTENT_LENGTH (ataques DoS) e emprega a função allowed_file().


9. TESTES E VALIDAÇÃO

O presente capítulo descreve o plano de testes executado para atestar a estabilidade, segurança e performance da plataforma LabCultural. A validação dividiu-se em ensaios manuais exploratórios, testes automatizados de comportamento lógico e aferição de compatibilidade visual.


9.1 Testes Funcionais

De modo a garantir que os Requisitos Funcionais delineados no Capítulo 2 operam em conformidade orgânica com os fluxos previstos, foi estabelecida a seguinte matriz de testes funcionais orientados ao utilizador. A coluna de evidência remete para a documentação de suporte (capturas de ecrã/anexos) entregue formalmente junto com o projeto.

ID do Teste | Funcionalidade | Cenário | Resultado Esperado | Resultado Obtido | Evidência / Observações
--- | --- | --- | --- | --- | ---
TF01 | Autenticação | Login com credenciais de administrador válidas. | Criação de sessão global e redirecionamento para o dashboard. | Passou | Anexo 1
TF02 | Autenticação | Acesso direto a rota protegida via URL sem sessão ativa. | Interceção imediata pelo decorator e redirecionamento. | Passou | Anexo 2
TF03 | CRUD Eventos | Submissão de formulário com omissão intencional de campos. | Bloqueio da submissão com mensagens de erro precisas. | Passou | Anexo 3
TF04 | Bilheteira | Inscrição num evento com e-mail não institucional. | Rejeição assíncrona pelo validador da API no cliente. | Passou | Anexo 4
TF05 | Bilheteira | Inscrição duplicada no mesmo espetáculo com o mesmo e-mail. | O sistema deteta o registo prévio e impede a submissão. | Passou | Anexo 5
TF06 | Mapa de Sala | Seleção de um lugar previamente reservado. | O clique não surte efeito (estado inalterado). Validação dupla. | Passou | Anexo 6
TF07 | API REST | Consulta ao endpoint de eventos parametrizando uma categoria. | Devolução estrita de um payload JSON contendo os eventos. | Passou | Anexo 7
TF08 | Email / SMTP | Finalização do fluxo de requisição de livro para "Aprovado". | Envio transparente de e-mail ao utilizador contendo o código gerado. | Passou | Anexo 8


9.2 Testes Unitários e de Integração

No âmbito de implementação de boas práticas de engenharia de software — vital em LPP — a fiabilidade de componentes estruturais, de segurança e de algoritmia foi validada através da formulação de testes automatizados modulares com recurso à framework `pytest`. Apresentam-se em seguida três exemplificações centrais efetuadas aos componentes vitais da plataforma.

Teste de Robustez Criptográfica (Unitário). O teste comprova matematicamente que a introdução contínua de "salts" no armazenamento protege *passwords* idênticas de gerarem *hashes* visuais idênticos, garantindo paralelamente que o comparador valida a string plana corretamente face à cifra encriptada.

```python
def test_bcrypt_salting_efficiency():
    password_plana = "AdminLabCultural123!"
    # Dois hashes sucessivos para a mesma chave
    hash1 = bcrypt.hashpw(password_plana.encode('utf-8'), bcrypt.gensalt())
    hash2 = bcrypt.hashpw(password_plana.encode('utf-8'), bcrypt.gensalt())
    
    # Salting obriga a resultados sempre divergentes
    assert hash1 != hash2  
    # Mas a string original prova inequivocamente pertencer a ambos
    assert bcrypt.checkpw(password_plana.encode('utf-8'), hash1) is True
```

Teste do Validador de Domínio Institucional (Unitário). Demonstra a fiabilidade da Regular Expression (RegEx) no módulo de segurança (`app/utils/security.py`) em triar de forma binária o acesso aos serviços vitais com e-mails lícitos (ispgaya.pt) ou intrusões camufladas:

```python
def test_validador_email_institucional():
    # Cenário Positivo: E-mail académico válido
    assert validar_email("aluno2024@ispgaya.pt") is True
    # Cenário Positivo: E-mail docente válido
    assert validar_email("professor@ispgaya.pt") is True
    
    # Cenário Negativo: Domínio externo genérico (não autorizado)
    assert validar_email("aluno@gmail.com") is False
    # Cenário Negativo: Injeção falaciosa e bypass sem hostname
    assert validar_email("<script>alert(1)</script>@ispgaya.pt") is False
```

Teste de Integração da Interface de Programação REST (Integração). Simulação programática de um cliente HTTP que consome os endpoints nativos do LabCultural. Garante a integridade, resiliência do protocolo de resposta e modelação da matriz JSON enviada para o website.

```python
def test_api_get_categorias_integration(client):
    response = client.get('/api/v1/categorias')
    
    # Valida código padrão de sucesso do servidor
    assert response.status_code == 200
    
    dados = response.get_json()
    # Verifica a estrutura devolvida é um Array coerente e populado
    assert isinstance(dados, list)
    assert len(dados) > 0
    # Valida as chaves fulcrais presentes na formatação JSON para os cards do frontend
    assert "nome" in dados[0] and "cor" in dados[0]
```


9.3 Testes de Responsividade

A responsividade da plataforma foi testada em três resoluções representativas:

Desktop (1920x1080). Todas as páginas apresentam o layout completo com múltiplas colunas. O menu principal é apresentado na horizontal. As grelhas de cards utilizam 3 colunas fluídas e os banners adaptam-se com integridade visual total.

Tablet (768x1024). O layout adapta-se automaticamente, reduzindo para 2 colunas nas grelhas de cards. O menu principal mantém-se visível, mas com espaçamentos estrategicamente ajustados para otimização da área útil.

Mobile (375x667). O layout comuta inteligentemente para coluna única (stack). O menu principal colapsa para formato *hamburger* poupando *viewport*. O mapa de sala interativo do teatro foi rigorosamente avaliado, confirmando o aparecimento de transição por *scroll* horizontal (*overflow*) enquanto mantém os lugares-botão perfeitamente operáveis e dimensionados (*touch targets* validados segundo guidelines de mobile UX).


9.4 Validação de Formulários

Todos os formulários da plataforma implementam validação em duas camadas arquitetónicas para tolerância a falhas:

Validação *client-side* (JavaScript). Campos obrigatórios são verificados assincronamente antes da operação de POST. O formato do e-mail é validado à medida que o utilizador atua. Campos com discrepâncias recebem destaque visual (borda vermelha) e inibem as ações *submit* preventivamente para abrandar sobrecarga do lado do servidor.

Validação *server-side* (Python). Todo o objeto de payload é dissecado nativamente no controlador. Os dados sofrem ação do modulo de sanitização antes de qualquer script de acesso de memória base. Numa situação remota em que scripts do lado do cliente se vejam contornados por via ardilosa, a arquitetura Python sobrepõe-se em soberania defensiva, impedindo a injeção. O utilizador recebe um flash error com retenção do preenchimento base em *sandbox*.


9.5 Compatibilidade de Browsers

A plataforma foi sujeita a verificações de tolerância nos motores de renderização líderes de mercado, operando nas suas mais recentes arquiteturas estáveis:

Google Chrome (versão 126 / motor Blink). Todas as funcionalidades operaram em pleno rigor, incidindo sem erro sob processamentos interativos intensos como gráficos *Chart.js*, *sliders Swiper.js*, interatividade DOM intensiva do mapa de lugares do clube de teatro e submissões com promessas *async* no Chatbot Gemini.

Mozilla Firefox (versão 128 / motor Gecko). Rendimento gráfico robusto e sem latências percecionadas; todas as instâncias que manipulam fetch API atuaram eficientemente. Modais em camada visual superior foram dispostos geometricamente de forma correta e sem quebra (Z-index coerente).

Safari iOS (versão 17 / motor WebKit). O comportamento responsivo para os ecrãs móveis atuou com conformidade rigorosa. Sublinha-se a consistência do modelo `localStorage` para retenção permanente das preferências relativas à política estrita do banner modal de consentimento de cookies sem amnésia pós fecho da aplicação.


10. CONCLUSÃO


10.1 Matriz de Cobertura de Requisitos

O presente projeto cumpriu taxativamente as diretrizes do enunciado prático para as disciplinas de LPP e ATW. O grau de cumprimento técnico é explicitado na seguinte matriz de cobertura face aos Requisitos Funcionais (RF) arquitetados na fase de engenharia:

Requisito Funcional (RF) | Cumprido | Estratégia de Implementação (Como)
--- | --- | ---
RF01 - Plataforma com Identidade ISPGAYA | Sim | Reprodução fidedigna do CSS (Tailwind), paleta cromática e clonagem exata do *widget* de Cookies do domínio original.
RF02 - Clube de Leitura c/ Requisições | Sim | Criação de catálogo dinâmico via SQLite e máquina de estados para empréstimos gerida nativamente no controlador administrativo.
RF03 - Bilheteira Digital do Teatro | Sim | Algoritmo Python para mapear matrizes bidimensionais no Jinja2. Validação severa de concorrência e transação segura na base de dados para impedir *overbooking*.
RF04 - Geração de Tickets c/ QR Code | Sim | Orquestração da biblioteca `fpdf2` + `qrcode` num endpoint backend devolvendo um documento imutável e despachado via SMTP.
RF05 - Controlo de Acessos Administrador | Sim | Implementação robusta do Padrão *Decorator* (`@login_required`, `@role_required`) injetando proteção preventiva e RBAC nas rotas.
RF06 - Integração IA (Google Gemini) | Sim | Chamadas assíncronas `fetch` (JS) a um endpoint protegido Flask que consome os tokens de IA, mascarando a Chave de API do cliente.


10.2 Métricas do Projeto (Engenharia de Software)

De forma a quantificar o volume tecnológico empregue na materialização do "LabCultural", extraiu-se uma radiografia analítica do código-fonte. Estes numéricos sublinham a complexidade de um ecossistema construído de raiz sem CMS de suporte:

Métrica | Quantidade | Detalhe Estrutural
--- | --- | ---
Linhas de Código Fonte (LOC) | ~ 5.300 | 2.100 linhas em pura arquitetura Python e 3.200 em Views Jinja2 (HTML/CSS/JS).
Total de Ficheiros Modulares | 48 | 18 scripts de Lógica/Modelos, 24 templates HTML de interface e 6 estáticos nativos.
Endpoints Definidos (Rotas) | 37 | Repartidos por *Blueprints* independentes: Frontoffice, Backoffice e API REST.
Tabelas Relacionais | 12 | Normalizadas (3NF) englobando sistema de Perfis (Roles), logs, catálogo e fluxos de reservas isoladas.


10.3 Dificuldades Encontradas

A integração visual com o portal do ISPGAYA representou o primeiro desafio significativo, dado que o website oficial utiliza uma estrutura e estilos proprietários que tiveram de ser submetidos a engenharia reversa no DevTools e replicados manualmente de raiz.

A migração entre SQLite e MySQL exigiu o desenvolvimento de uma camada de abstração (Decorator) personalizada para traduzir diferenças de sintaxe severas entre os dois motores de base de dados, superando as limitações dos placeholders de parâmetros.

A geração autómata de bilhetes PDF com QR Code embebido obrigou a uma curva de aprendizagem súbita com bibliotecas periféricas (`fpdf2`, `qrcode`) e forçou o grupo a resolver limitações de layout para desenhar um simulacro de ticket vertical real e enviá-lo sem que o browser ficasse pendurado à espera.


10.4 Trabalho Futuro

Embora a plataforma fechada garanta as necessidades correntes, existem frentes de evolução corporativa a serem consideradas numa hipotética v2.0:

1. Integração com APIs externas de agendamento (Google Calendar API, Eventbrite) para auto-alimentação sazonal da programação cultural fora de portas.
2. Evoluir a interface atual para uma arquitetura PWA (Progressive Web App), permitindo o cache offline dos utilizadores e a instalação num dispositivo móvel com *feeling* nativo (Service Workers).
3. Internacionalização imperativa da plataforma (Dicionários pt/en) providenciando o acolhimento digital imediato a estudantes do panorama Erasmus.


10.5 Oportunidades de Melhoria Arquitetónica (Visão Crítica)

Numa perspetiva de autoavaliação e maturidade de engenharia face aos padrões da indústria, identificam-se três eixos de evolução arquitetónica que, embora dispendiosos no contexto académico imediato, seriam imperativos num ambiente corporativo de produção:

1. A Camada de Abstração SQL (Integração ORM). A criação da classe `SQLiteCursorWrapper` foi uma solução de engenharia criativa para traduzir *placeholders* (`%s` vs `?`) e garantir o requisito avaliativo de compatibilidade cruzada imediata. Todavia, em aplicações empresariais, escrever *wrappers* manuais para gerir dialetos SQL é insustentável a longo prazo. A transição para um ORM (*Object-Relational Mapper*) como o SQLAlchemy seria a norma da indústria para abstrair por completo o motor de base de dados e prevenir eventuais bugs de manipulação de strings na camada transacional.

2. Segurança e Desacoplamento da API REST. Foi desenvolvida uma API RESTful (`/api/v1/`) veloz que alimenta o *front-end* de forma assíncrona. Contudo, em APIs modernas desacopladas, o padrão corporativo determina a rejeição de autenticação baseada em sessões web/cookies para endpoints API em favor de um modelo *stateless* baseado em tokens (JWT - *JSON Web Tokens*). Adotar esta metodologia de autenticação isolada seria o próximo salto evolutivo da infraestrutura de segurança.

3. Escalabilidade de Tabelas de Entidades (Normalização Plena). Estruturar tabelas independentes (e.g., `membros_leitura`, `membros_teatro`) simplificou o raciocínio das queries de leitura no momento de conceção. Não obstante, se a instituição aprovar a génese de 10 novos clubes de índole diversa a curto prazo, a base de dados ver-se-ia refém de alterações estruturais manuais e cíclicas. Uma tabela agnóstica única, como `membros_clube`, suportada por uma chave estrangeira genérica para `clube_id`, consistiria numa arquitetura de base de dados visivelmente mais elástica e escalável.


10.6 Reflexão Pessoal e Aprendizagens

O desenvolvimento deste projeto de larga escala cimentou drasticamente o conhecimento teórico, forçando o grupo a lidar com problemas de engenharia de software reais, imprevisíveis e com interdependência de paradigmas de programação.

Do ponto de vista técnico e resolutivo, sublinha-se a ocorrência de obstáculos marcantes que refinaram a nossa proficiência em Python e estruturação Web:

1. Problemas de Sincronização no Mapa de Sala (Concurrency): Inicialmente, defrontámo-nos com o risco crítico de *overbooking* no teatro, pois o mapa de assentos client-side podia ficar desatualizado se múltiplos utilizadores clicassem na mesma cadeira com diferença de segundos. A resolução forçou-nos a ir para além do Javascript visual: criamos uma verificação transacional rígida no backend em que o algoritmo Python, durante o `POST`, bloqueia a base de dados em tempo real, executa um `SELECT` final e devolve um flash error gracioso ("Este lugar acabou de ser reservado") caso o lugar já não esteja efetivamente livre, protegendo a bilheteira na camada lógica e não apenas visual.

2. Fugas de Dados nas Sessões Flask: Numa iteração primária, confundimos fechar o *tab* do browser com a expiração real do utilizador, resultando em reentradas de administrador indevidas por via do cache do Cookie criptografado persistir no ficheiro do browser. Resolvemos a falha estruturando um verdadeiro controlador de *logout* que ativa a diretiva `session.clear()` e reajustamos os *decorators* de autenticação para avaliarem permanentemente contra o SQLite se a flag booleana `admin_ativo = 1` ainda é lícita, trancando falhas de acesso de sessão estática.

3. Armazenamento de Arrays e Normalização: Guardar listas de cadeiras múltiplas selecionadas pelo aluno (ex: `['A1', 'A2', 'B1']`) esbarrou nas limitações orgânicas de bases de dados SQL tradicionais que não comportam campos Array. A solução viável para manter as strings pesquisáveis exigiu afinar conhecimentos do paradigma de programação imperativa, efetuando *loops*, *list comprehensions* e tratamento com a library `json` em Python para injetar a lista num formato texto legível na base de dados (e extraí-la inversamente para as listagens de reservas).

A orquestração de ecossistemas (Flask, REST, Tailwind, Vanilla JS e SQL) num monólito testável validou por completo as competências semestrais. O grupo considera este LabCultural um produto pronto para a esfera produtiva, consubstanciando o fecho ideal de ciclo das UC's envolvidas.
