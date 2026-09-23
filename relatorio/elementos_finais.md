# ELEMENTOS PRÉ E PÓS-TEXTUAIS (Para colar no Word)

---
## Para as primeiras páginas do Word (logo a seguir aos índices):

### RESUMO

O presente projeto académico visa a concetualização, desenho e desenvolvimento da plataforma web "Laboratório Cultural" para o Instituto Superior Politécnico Gaya (ISPGAYA). Este trabalho foi realizado de forma integrada para o cumprimento dos objetivos das unidades curriculares de Aplicações e Tecnologias Web (ATW) e Linguagens e Paradigmas da Programação (LPP). 
A plataforma desenvolvida centraliza a oferta cultural da instituição, oferecendo três vertentes principais: um Clube de Leitura com catálogo virtual e sistema de requisições de obras; um Clube de Teatro suportado por um motor de bilheteira digital complexo que integra um mapa interativo de assentos e geração de bilhetes em PDF com QR Code; e a Tuna Académica. 
Do ponto de vista arquitetónico, o projeto consagra a aplicação rigorosa de paradigmas de programação (Orientado a Objetos, Funcional e Imperativo) e Padrões de Design de Software (MVC, Factory, Repository, Decorator) num ecossistema Python com a framework Flask. O front-office foi desenvolvido com foco na usabilidade, garantindo responsividade via Tailwind CSS e interatividade assíncrona com JavaScript (AJAX). O back-office conta com um painel administrativo seguro gerido por Controlo de Acessos Baseado em Perfis (RBAC), mecanismos de proteção contra injeções XSS e SQL, e encriptação *bcrypt*. Destaca-se ainda a integração avançada de uma IA conversacional (Chatbot via API Google Gemini) como funcionalidade extracurricular de apoio aos estudantes.

**Palavras-chave:** Aplicações Web, Engenharia de Software, Flask, Python, Padrões de Design, Bilheteira Digital, Inteligência Artificial.


### ABSTRACT

This academic project aims to conceptualize, design, and develop the "Laboratório Cultural" web platform for the Instituto Superior Politécnico Gaya (ISPGAYA). This work was carried out in an integrated manner to fulfill the objectives of the Web Applications and Technologies (ATW) and Programming Languages and Paradigms (LPP) courses.
The developed platform centralizes the institution's cultural offerings, featuring three main areas: a Reading Club with a virtual catalog and book borrowing system; a Theater Club supported by a complex digital ticketing engine that integrates an interactive seating map and PDF ticket generation with QR Code; and the Academic Tuna.
Architecturally, the project enshrines the rigorous application of programming paradigms (Object-Oriented, Functional, and Imperative) and Software Design Patterns (MVC, Factory, Repository, Decorator) in a Python ecosystem using the Flask framework. The front-office was developed with a focus on usability, ensuring responsiveness via Tailwind CSS and asynchronous interactivity with JavaScript (AJAX). The back-office features a secure administrative panel managed by Role-Based Access Control (RBAC), protection mechanisms against XSS and SQL injections, and *bcrypt* encryption. Notably, it also includes the advanced integration of a conversational AI (Chatbot via Google Gemini API) as an extracurricular feature to support students.

**Keywords:** Web Applications, Software Engineering, Flask, Python, Design Patterns, Digital Ticketing, Artificial Intelligence.

---
## Para o final do Word (logo antes dos Anexos):

### MANUAL DE INSTALAÇÃO E EXECUÇÃO

O processo de compilação e execução da plataforma "Laboratório Cultural" foi desenhado para ser célere e universal em ambientes Windows, macOS ou Linux. Para avaliar o projeto, o docente deverá seguir as seguintes instruções técnicas:

**1. Requisitos Prévios do Sistema**
*   **Linguagem:** Python 3.10 ou superior.
*   **Gestor de Pacotes:** `pip` atualizado.
*   **Base de Dados:** Por defeito, a aplicação utiliza SQLite3 (incluído nativamente no Python, sem necessidade de servidores locais como o XAMPP, embora o código esteja estruturado para comutar para MySQL mudando um simples parâmetro).

**2. Preparação do Ambiente**
1.  Extrair a pasta raiz do projeto para um diretório local do computador.
2.  Abrir a linha de comandos (Terminal, PowerShell ou CMD) e navegar até à raiz do projeto onde se encontra o ficheiro `start.py`.

**3. Instalação de Dependências**
De modo a instalar a totalidade do ecossistema utilizado (Flask, Bcrypt, FPDF2, QRCode, Google Generative AI), executar o seguinte comando na linha de comandos:
> `pip install -r requirements.txt`

*(Nota: É fortemente aconselhada a criação de um Virtual Environment prévio através do comando `python -m venv venv` e a sua ativação para não comprometer as dependências globais do sistema).*

**4. Execução do Servidor**
Arrancar a aplicação através da evocação direta do script de inicialização do servidor de desenvolvimento:
> `python start.py`

Se a execução for bem-sucedida, o terminal indicará que o Flask está operacional no endereço `http://127.0.0.1:5000/`.

**5. Credenciais de Acesso ao Backoffice**
A aplicação encarrega-se de criar a base de dados `lab_cultural.db` automaticamente (e as suas respetivas tabelas) caso esta não exista.
*   **Front-office:** Aceder a `http://localhost:5000/` através de qualquer browser atualizado.
*   **Back-office Administrativo:** Aceder a `http://localhost:5000/admin/login` e utilizar as seguintes credenciais de desenvolvimento pré-configuradas:
    *   **Username:** `admin`
    *   **Password:** `admin`


### REFERÊNCIAS BIBLIOGRÁFICAS E WEBGRAFIA

(Formatação construída em conformidade com as diretrizes da norma APA 7ª Edição)

FPDF2 Developers. (2024). *FPDF2: A library for PDF document generation under Python*. GitHub Pages. Acedido em https://py-pdf.github.io/fpdf2/

Google. (2024). *Google AI for Developers: Gemini API Documentation*. Acedido em https://ai.google.dev/docs

Grinberg, M. (2018). *Flask Web Development: Developing Web Applications with Python* (2ª Ed.). O'Reilly Media.

Mozilla Developer Network [MDN]. (2024). *Web technology for developers: JavaScript, HTML, CSS*. Acedido em https://developer.mozilla.org/

OWASP Foundation. (2021). *OWASP Top 10:2021 - The Ten Most Critical Web Application Security Risks*. Acedido em https://owasp.org/Top10/

Pallets Projects. (2024). *Flask Documentation (Versão 3.0.x)*. Acedido em https://flask.palletsprojects.com/

Python Software Foundation. (2024). *The Python Standard Library Documentation (Versão 3.12)*. Acedido em https://docs.python.org/3/

Swiper Studio. (2024). *Swiper: The Most Modern Mobile Touch Slider API*. Acedido em https://swiperjs.com/swiper-api

Tailwind Labs. (2024). *Tailwind CSS Documentation: Rapidly build modern websites without ever leaving your HTML*. Acedido em https://tailwindcss.com/docs
