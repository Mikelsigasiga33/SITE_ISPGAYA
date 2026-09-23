# 📋 Guião de Evidências de Testes (Anexos 1 a 8 e Anexo C)

> **Instruções para o Word**: Crie uma secção no fim do seu documento Word chamada **ANEXOS**. Utilize os cabeçalhos abaixo para estruturar cada anexo e tire capturas de ecrã do seu site local a funcionar para colar em cada respetiva zona. 
> 
> *Nota: Os testes TF01 a TF08 no Capítulo 9.1 já remetem para estes Anexos, pelo que isto completará o relatório perfeitamente.*

---

# ANEXOS

## ANEXO 1: Evidência do Teste TF01 — Autenticação de Administrador Válida

**Objetivo**: Validar a criação da sessão global e redirecionamento correto para o dashboard administrativo.

*   **Instruções de Captura**: 
    1. Aceda a `http://localhost:5000/admin/login`.
    2. Introduza as credenciais: Utilizador `admin` e palavra-passe `admin`.
    3. Após fazer login, tire uma captura de ecrã do **Dashboard Administrativo** exibindo os gráficos e a indicação de que o utilizador está autenticado.
*   **Legenda no Word**: 
    > *Figura A1: Painel do Dashboard Administrativo (Back-office) renderizado com sucesso após autenticação válida.*

---

## ANEXO 2: Evidência do Teste TF02 — Proteção de Rotas Sem Sessão Ativa

**Objetivo**: Validar a interceção de acesso indevido a rotas administrativas através do decorator `@login_required`.

*   **Instruções de Captura**:
    1. Feche o browser ou abra uma janela anónima.
    2. Tente aceder diretamente à rota `http://localhost:5000/admin/eventos` sem fazer login.
    3. Tire uma captura de ecrã da página de login (`/admin/login`) com a mensagem flash de aviso indicando que o acesso é restrito e exige login.
*   **Legenda no Word**:
    > *Figura A2: Redirecionamento automático e bloqueio de acesso a rota protegida sem sessão válida.*

---

## ANEXO 3: Evidência do Teste TF03 — Validação de Campos Obrigatórios (CRUD)

**Objetivo**: Validar o bloqueio de submissão do formulário na omissão de campos requeridos.

*   **Instruções de Captura**:
    1. No Back-office, aceda à criação de um Evento (`/admin/eventos/criar`).
    2. Deixe o campo "Título" ou "Data" vazio e clique em "Gravar" ou "Submeter".
    3. Tire uma captura de ecrã mostrando os alertas vermelhos de validação do browser (HTML5) ou as mensagens de erro de validação do backend (Flask flash errors).
*   **Legenda no Word**:
    > *Figura A3: Formulário de criação de evento exibindo alertas visuais de erro de validação de campos obrigatórios.*

---

## ANEXO 4: Evidência do Teste TF04 — Validação de Domínio de E-mail

**Objetivo**: Validar o bloqueio de inscrições com e-mails externos não académicos (@ispgaya.pt).

*   **Instruções de Captura**:
    1. No Front-office, vá à página de um Evento ou do Teatro e tente inscrever-se usando um e-mail pessoal (ex: `aluno@gmail.com` ou `aluno@outlook.pt`).
    2. Tire uma captura de ecrã da mensagem de erro a vermelho que aparece na página (ex: *"Apenas são permitidos e-mails com domínio @ispgaya.pt"*).
*   **Legenda no Word**:
    > *Figura A4: Rejeição imediata do formulário de inscrição por uso de domínio de e-mail externo não autorizado.*

---

## ANEXO 5: Evidência do Teste TF05 — Prevenção de Inscrições Duplicadas

**Objetivo**: Validar o controlo lógico contra múltiplas inscrições da mesma pessoa no mesmo espetáculo.

*   **Instruções de Captura**:
    1. Inscreva-se num espetáculo de teatro usando o e-mail institucional `aluno@ispgaya.pt`.
    2. Tente submeter uma segunda inscrição exatamente para o mesmo espetáculo com o mesmo e-mail `aluno@ispgaya.pt`.
    3. Tire uma captura de ecrã do erro apresentado (ex: *"Este e-mail já se encontra registado neste espetáculo"*).
*   **Legenda no Word**:
    > *Figura A5: Alerta do sistema impedindo a duplicação de inscrição para a mesma entidade/sessão.*

---

## ANEXO 6: Evidência do Teste TF06 — Mapa de Lugares Ocupados (Teatro)

**Objetivo**: Confirmar que lugares previamente reservados aparecem desabilitados e não são selecionáveis.

*   **Instruções de Captura**:
    1. Aceda à página de reservas de um espetáculo de teatro no Front-office.
    2. Certifique-se de que existem lugares reservados (quadrados a vermelho no mapa). Tente clicar num desses lugares.
    3. Tire uma captura de ecrã do **Mapa de Sala** mostrando o aspeto dos lugares ocupados (vermelho) vs disponíveis (verde) vs selecionados (laranja).
*   **Legenda no Word**:
    > *Figura A6: Visualização do Mapa de Assentos com distinção visual de estados (Livre, Ocupado, Selecionado).*

---

## ANEXO 7: Evidência do Teste TF07 — Resposta da API REST em formato JSON

**Objetivo**: Validar o correto funcionamento e estrutura do endpoint público da API.

*   **Instruções de Captura**:
    1. No browser, aceda a `http://localhost:5000/api/v1/eventos`.
    2. Tire uma captura de ecrã do payload JSON devolvido pelo servidor (ou use uma ferramenta como Postman). O browser moderno costuma formatar o JSON de forma legível.
*   **Legenda no Word**:
    > *Figura A7: Resposta estruturada em formato JSON do endpoint público da API de eventos.*

---

## ANEXO 8: Evidência do Teste TF08 — Envio de E-mail de Confirmação por SMTP

**Objetivo**: Validar a integração com o servidor SMTP (Gmail) e envio real de e-mails de confirmação.

*   **Instruções de Captura**:
    1. Efetue uma inscrição ou requisição de livro com um e-mail institucional do qual tenha acesso à caixa de entrada (ou use a password do Gmail de desenvolvimento para testar o envio para a sua própria caixa).
    2. Aceda à caixa de e-mail e abra a mensagem enviada pelo Laboratório Cultural contendo o código QR e o bilhete.
    3. Tire uma captura de ecrã do e-mail recebido.
*   **Legenda no Word**:
    > *Figura A8: E-mail de confirmação real recebido na caixa de entrada do utilizador com o detalhe do bilhete.*

---

# ANEXO C: Diagrama Entidade-Relação Expandido

*(Nota: Copie a imagem gerada a partir do ficheiro `relatorio/diagrama_er.md` e cole-a em alta resolução aqui).*

*   **Legenda no Word**:
    > *Figura AC: Esquema relacional e dicionário de ligações lógicas da base de dados do Laboratório Cultural.*
