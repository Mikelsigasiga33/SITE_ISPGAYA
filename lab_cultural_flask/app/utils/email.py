import smtplib
import qrcode
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import Config


class EmailService:
    @staticmethod
    def enviar_bilhete(email_destino, nome_aluno, espetaculo, codigo_inscricao):
        """Gera um bilhete PDF profissional (estilo BOL) e envia por e-mail."""

        from fpdf import FPDF

        # ── 1. Gerar QR Code em memória ──
        qr = qrcode.make(codigo_inscricao)
        qr_buffer = io.BytesIO()
        qr.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # Guardar temporariamente para o fpdf ler
        import tempfile, os
        qr_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        qr_tmp.write(qr_buffer.read())
        qr_tmp.close()

        # ── 2. Dados do espetáculo ──
        titulo = espetaculo.get('titulo', 'Evento')
        data_str = espetaculo['data_evento'].strftime('%d/%m/%Y') if espetaculo.get('data_evento') else 'A anunciar'
        hora_str = str(espetaculo.get('hora', '21:00'))
        local_str = espetaculo.get('local') or 'Auditório ISPGAYA'

        # ── 3. Construir PDF ──
        pdf = FPDF('P', 'mm', (100, 250))  # formato bilhete vertical
        pdf.add_page()
        pdf.set_auto_page_break(False)

        # --- Barra superior laranja ---
        pdf.set_fill_color(249, 115, 22)
        pdf.rect(0, 0, 100, 32, 'F')

        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(5, 5)
        pdf.cell(90, 4, 'BILHETEIRA LAB CULTURAL', align='L')

        pdf.set_font('Helvetica', '', 6)
        pdf.set_xy(5, 10)
        pdf.cell(90, 4, 'ISPGAYA - Instituto Superior Politecnico Gaya', align='L')

        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(5, 18)
        pdf.cell(90, 8, 'BILHETE', align='L')

        # --- Título do evento ---
        pdf.set_text_color(30, 30, 30)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_xy(5, 38)
        pdf.multi_cell(90, 6, titulo, align='L')

        y_after_title = pdf.get_y() + 4

        # --- Linha separadora ---
        pdf.set_draw_color(230, 230, 230)
        pdf.line(5, y_after_title, 95, y_after_title)

        # Como não há lugares marcados, tratamos como Entrada Geral
        lugares_str = "Geral"
        
        # --- Detalhes do evento ---
        y = y_after_title + 4
        details = [
            ('DATA', data_str),
            ('HORA', hora_str),
            ('LOCAL', local_str),
            ('TITULAR', nome_aluno),
            ('EMAIL', email_destino),
        ]
        if lugares_str:
            details.append(('ENTRADA', lugares_str))

        for label, value in details:
            pdf.set_font('Helvetica', 'B', 6)
            pdf.set_text_color(160, 160, 160)
            pdf.set_xy(5, y)
            pdf.cell(25, 4, label, align='L')

            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(30, 30, 30)
            pdf.set_xy(30, y)
            pdf.cell(65, 4, value, align='L')
            y += 9

        # --- Linha tracejada (corte) ---
        y += 4
        pdf.set_draw_color(200, 200, 200)
        for x_pos in range(5, 95, 3):
            pdf.line(x_pos, y, x_pos + 1.5, y)

        # --- QR Code ---
        y += 6
        pdf.image(qr_tmp.name, x=25, y=y, w=50, h=50)
        y += 54

        # --- Código de inscrição ---
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(30, 30, 30)
        pdf.set_xy(5, y)
        pdf.cell(90, 5, f'ID: {codigo_inscricao}', align='C')
        y += 8

        # --- Nota de rodapé ---
        pdf.set_font('Helvetica', '', 6)
        pdf.set_text_color(160, 160, 160)
        pdf.set_xy(5, y)
        pdf.cell(90, 3, 'Apresente este bilhete na entrada.', align='C')
        pdf.set_xy(5, y + 4)
        pdf.cell(90, 3, 'Bilhete pessoal e intransmissivel.', align='C')

        pdf_content = pdf.output()

        # Limpar ficheiro temporário do QR
        os.unlink(qr_tmp.name)

        # ── 4. Verificar se temos SMTP configurado ──
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Bilhete PDF gerado para {email_destino} ---")
            print(f"Espetaculo: {titulo} | Codigo: {codigo_inscricao}\n")
            return True

        # ── 5. Compor e-mail HTML profissional ──
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Bilheteira Lab Cultural <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"O teu bilhete: {titulo}"

        # Corpo HTML simples e profissional
        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <p style="margin:0;font-size:11px;color:rgba(255,255,255,0.8);letter-spacing:1px;">BILHETEIRA LAB CULTURAL</p>
        <h1 style="margin:6px 0 0;font-size:20px;color:#fff;">Reserva Confirmada</h1>
    </div>

    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">
            Ola <strong>{nome_aluno}</strong>, o teu bilhete para o espetaculo abaixo esta confirmado.
        </p>

        <table style="width:100%;border-collapse:collapse;margin:0 0 20px;">
            <tr>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:11px;color:#999;width:80px;">EVENTO</td>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:13px;font-weight:bold;">{titulo}</td>
            </tr>
            <tr>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:11px;color:#999;">DATA</td>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:13px;">{data_str}</td>
            </tr>
            <tr>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:11px;color:#999;">HORA</td>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:13px;">{hora_str}</td>
            </tr>
            <tr>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:11px;color:#999;">LOCAL</td>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:13px;">{local_str}</td>
            </tr>
            {f'''<tr>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:11px;color:#999;">ENTRADA</td>
                <td style="padding:8px 0;border-bottom:1px solid #f3f3f3;font-size:13px;font-weight:bold;">{lugares_str}</td>
            </tr>''' if lugares_str else ''}
            <tr>
                <td style="padding:8px 0;font-size:11px;color:#999;">CODIGO</td>
                <td style="padding:8px 0;font-size:13px;font-weight:bold;color:#f97316;">{codigo_inscricao}</td>
            </tr>
        </table>

        <p style="font-size:12px;color:#666;margin:0 0 4px;">
            O teu bilhete em PDF segue em anexo a este e-mail.
        </p>
        <p style="font-size:11px;color:#999;margin:0;">
            Apresenta-o na entrada do auditorio (ecra ou impresso).
        </p>
    </div>

    <p style="text-align:center;font-size:10px;color:#bbb;margin-top:16px;">
        ISPGAYA &middot; Laboratorio Cultural &middot; Clube de Teatro
    </p>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))

        # Anexar o PDF
        part = MIMEApplication(pdf_content, Name=f"bilhete_{codigo_inscricao}.pdf")
        part['Content-Disposition'] = f'attachment; filename="bilhete_{codigo_inscricao}.pdf"'
        msg.attach(part)

        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            print(f"[OK] E-mail enviado para {email_destino}")
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail: {e}")
            return False

    @staticmethod
    def enviar_resposta_membro(email_destino, nome, estado):
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Email de resposta de recrutamento enviado para {email_destino} ---")
            print(f"Nome: {nome} | Novo Estado: {estado}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Clube de Teatro ISPGAYA <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"A tua inscrição no Clube de Teatro"

        texto_decisao = ""
        cor_decisao = ""
        if estado == "Aceite":
            texto_decisao = "Parabéns! Foste <strong>aceite</strong> no Clube de Teatro. Em breve receberás mais informações sobre o horário dos ensaios."
            cor_decisao = "#059669" # Verde
        else:
            texto_decisao = "Lamentamos, mas neste momento a tua inscrição foi <strong>recusada/em espera</strong>. As vagas podem estar cheias, mas guardaremos o teu contacto para o futuro."
            cor_decisao = "#dc2626" # Vermelho

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Clube de Teatro</h1>
    </div>

    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">
            Olá <strong>{nome}</strong>,
        </p>
        <p style="margin:0 0 16px;font-size:14px;color:{cor_decisao};">
            {texto_decisao}
        </p>
        <p style="font-size:12px;color:#666;margin:0;">
            Obrigado pelo teu interesse no Laboratório Cultural.
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))

        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail de resposta: {e}")
            return False

    @staticmethod
    def enviar_confirmacao_sessao_leitura(email_destino, nome, tema, data_hora, local):
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Confirmacao sessao leitura para {email_destino} ---")
            print(f"Nome: {nome} | Sessao: {tema}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Clube de Leitura ISPGAYA <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"Confirmação: {tema}"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Clube de Leitura</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">A tua inscrição na sessão de leitura foi confirmada!</p>
        <ul style="font-size:13px; color:#555;">
            <li><strong>Tema:</strong> {tema}</li>
            <li><strong>Data e Hora:</strong> {data_hora}</li>
            <li><strong>Local:</strong> {local}</li>
        </ul>
        <p style="font-size:12px;color:#666;margin:0;margin-top:16px;">Vemo-nos lá!</p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail sessao leitura: {e}")
            return False

    @staticmethod
    def enviar_resposta_membro_leitura(email_destino, nome, estado):
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Email resposta leitura para {email_destino} ---")
            print(f"Nome: {nome} | Estado: {estado}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Clube de Leitura ISPGAYA <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"O teu interesse no Clube de Leitura"

        if estado == "Aceite":
            texto = "Excelente notícia! A tua inscrição no Clube de Leitura foi <strong>aceite</strong>. Fica atento às próximas sessões mensais!"
            cor = "#059669"
        else:
            texto = "Infelizmente, não podemos aceitar a tua inscrição no Clube de Leitura de momento. Entraremos em contacto se surgirem novas oportunidades."
            cor = "#dc2626"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Clube de Leitura</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;color:{cor};">{texto}</p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail: {e}")
            return False

    @staticmethod
    def enviar_confirmacao_requisicao_livro(email_destino, nome, titulo_livro, codigo):
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Confirmacao requisicao livro para {email_destino} ---")
            print(f"Nome: {nome} | Livro: {titulo_livro} | Codigo: {codigo}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Biblioteca Lab Cultural <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"Requisição de Livro: {titulo_livro}"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Biblioteca Lab Cultural</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">A tua requisição do livro <strong>{titulo_livro}</strong> foi recebida com sucesso!</p>
        <p style="font-size:16px; color:#f97316; font-weight:bold; text-align:center; padding:15px; border:2px dashed #f97316;">
            CÓDIGO: {codigo}
        </p>
        <p style="font-size:12px;color:#666;margin:0;margin-top:16px;">
            Apresenta este código na biblioteca para levantares o teu livro. Fica atento ao teu e-mail para a confirmação de disponibilidade.
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail requisicao livro: {e}")
            return False

    @staticmethod
    def enviar_requisicao_pendente(email_destino, nome, titulo_livro):
        """Email enviado quando o aluno faz o pedido (sem código - aguarda aprovação)."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Requisicao PENDENTE para {email_destino} ---")
            print(f"Nome: {nome} | Livro: {titulo_livro}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Biblioteca Lab Cultural <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"Requisição recebida: {titulo_livro}"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Biblioteca Lab Cultural</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">O teu pedido de requisição do livro <strong>{titulo_livro}</strong> foi recebido com sucesso!</p>
        <div style="background:#fef3c7;border:1px solid #fcd34d;padding:16px;border-radius:4px;text-align:center;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:#92400e;font-weight:bold;">
                ⏳ AGUARDA APROVAÇÃO
            </p>
            <p style="margin:8px 0 0;font-size:12px;color:#a16207;">
                O teu pedido será analisado pela equipa da biblioteca. Receberás um e-mail com o código de levantamento assim que for aprovado.
            </p>
        </div>
        <p style="font-size:12px;color:#666;margin:16px 0 0;">
            Obrigado pelo teu interesse na leitura!
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail requisicao pendente: {e}")
            return False

    @staticmethod
    def enviar_requisicao_recusada(email_destino, nome, titulo_livro):
        """Email enviado quando o admin recusa a requisição."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Requisicao RECUSADA para {email_destino} ---")
            print(f"Nome: {nome} | Livro: {titulo_livro}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Biblioteca Lab Cultural <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"Requisição não aprovada: {titulo_livro}"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Biblioteca Lab Cultural</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">Lamentamos informar que a tua requisição do livro <strong>{titulo_livro}</strong> não foi aprovada de momento.</p>
        <div style="background:#fee2e2;border:1px solid #fca5a5;padding:16px;border-radius:4px;text-align:center;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:#991b1b;font-weight:bold;">
                ✗ REQUISIÇÃO NÃO APROVADA
            </p>
            <p style="margin:8px 0 0;font-size:12px;color:#b91c1c;">
                O livro pode não estar disponível no momento ou existem outros pedidos prioritários. Tenta novamente mais tarde.
            </p>
        </div>
        <p style="font-size:12px;color:#666;margin:16px 0 0;">
            Obrigado pela tua compreensão. Continua a explorar o nosso catálogo!
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail requisicao recusada: {e}")
            return False
    @staticmethod
    def enviar_lembrete_entrega_livro(email_destino, nome, titulo_livro, data_limite):
        """Email de lembrete enviado quando falta 1 dia para a entrega."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Lembrete de entrega para {email_destino} ---")
            print(f"Nome: {nome} | Livro: {titulo_livro} | Prazo: {data_limite}\n")
            return True

        if isinstance(data_limite, str):
            from datetime import datetime
            try:
                dt = datetime.strptime(data_limite, '%Y-%m-%d %H:%M:%S')
                data_formatada = dt.strftime('%d/%m/%Y')
            except:
                data_formatada = data_limite
        else:
            data_formatada = data_limite.strftime('%d/%m/%Y')

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Biblioteca Lab Cultural <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"Lembrete: Entrega do livro {titulo_livro}"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f59e0b;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Lembrete de Devolução</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">Este é um lembrete automático de que o prazo de entrega do livro <strong>{titulo_livro}</strong> termina amanhã.</p>
        <div style="background:#fff7ed;border:1px solid #fdba74;padding:16px;border-radius:4px;text-align:center;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:#c2410c;font-weight:bold;">
                📅 PRAZO: {data_formatada}
            </p>
        </div>
        <p style="font-size:12px;color:#666;margin:16px 0 0;">
            Por favor, dirige-te à biblioteca para efetuares a entrega ou solicitares uma renovação, se aplicável.
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar lembrete de entrega: {e}")
            return False

    @staticmethod
    def enviar_codigo_expirado(email_destino, nome, titulo_livro):
        """Email enviado quando o código de levantamento expirou (1 dia)."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Código EXPIRADO para {email_destino} ---")
            print(f"Nome: {nome} | Livro: {titulo_livro}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Biblioteca Lab Cultural <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"Código expirado: {titulo_livro}"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#ef4444;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Código de Levantamento Expirado</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">O prazo de 24 horas para levantares o livro <strong>{titulo_livro}</strong> na biblioteca expirou.</p>
        <div style="background:#fef2f2;border:1px solid #fca5a5;padding:16px;border-radius:4px;text-align:center;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:#991b1b;font-weight:bold;">
                ⏰ CÓDIGO EXPIRADO
            </p>
            <p style="margin:8px 0 0;font-size:12px;color:#b91c1c;">
                O livro voltou a ficar disponível para outros alunos. Podes requisitá-lo novamente se desejares.
            </p>
        </div>
        <p style="font-size:12px;color:#666;margin:16px 0 0;">
            Obrigado pela tua compreensão.
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail código expirado: {e}")
            return False

    @staticmethod
    def enviar_confirmacao_membro_teatro_pendente(email_destino, nome):
        """Email enviado quando o aluno se inscreve no Clube de Teatro (aguarda aprovação)."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Confirmacao pendente Clube de Teatro para {email_destino} ---")
            print(f"Nome: {nome}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Clube de Teatro ISPGAYA <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = "Candidatura ao Clube de Teatro recebida"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Clube de Teatro ISPGAYA</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">A tua candidatura para te juntares ao <strong>Clube de Teatro</strong> do Laboratório Cultural foi recebida com sucesso!</p>
        
        <div style="background:#fef3c7;border:1px solid #fcd34d;padding:16px;border-radius:4px;text-align:center;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:#92400e;font-weight:bold;">
                ⏳ INSCRIÇÃO EM ANÁLISE
            </p>
            <p style="margin:8px 0 0;font-size:12px;color:#a16207;">
                O teu pedido está a ser avaliado pela nossa equipa. Receberás um e-mail com a decisão assim que o teu pedido for aceite ou recusado.
            </p>
        </div>
        
        <p style="font-size:12px;color:#666;margin:16px 0 0;">
            Obrigado pelo teu interesse e participação na vida académica do ISPGAYA!
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail de candidatura pendente: {e}")
            return False

    @staticmethod
    def enviar_confirmacao_membro_tuna_pendente(email_destino, nome):
        """Email enviado quando o aluno se inscreve na Tuna Académica (aguarda aprovação)."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Confirmacao pendente Tuna Académica para {email_destino} ---")
            print(f"Nome: {nome}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Tuna Académica ISPGAYA <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = "Candidatura à Tuna Académica recebida"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Tuna Académica ISPGAYA</h1>
    </div>
    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">Olá <strong>{nome}</strong>,</p>
        <p style="margin:0 0 16px;font-size:14px;">A tua candidatura para te juntares à <strong>Tuna Académica</strong> do Laboratório Cultural foi recebida com sucesso!</p>
        
        <div style="background:#fef3c7;border:1px solid #fcd34d;padding:16px;border-radius:4px;text-align:center;margin:16px 0;">
            <p style="margin:0;font-size:13px;color:#92400e;font-weight:bold;">
                ⏳ INSCRIÇÃO EM ANÁLISE
            </p>
            <p style="margin:8px 0 0;font-size:12px;color:#a16207;">
                O teu pedido está a ser avaliado pela nossa equipa. Receberás um e-mail com a decisão assim que o teu pedido for aceite ou recusado.
            </p>
        </div>
        
        <p style="font-size:12px;color:#666;margin:16px 0 0;">
            Obrigado pelo teu interesse e participação na vida académica do ISPGAYA!
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))
        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail de candidatura tuna pendente: {e}")
            return False

    @staticmethod
    def enviar_resposta_membro_tuna(email_destino, nome, estado):
        """Email enviado quando o admin aceita ou recusa um membro da Tuna."""
        if not all([Config.MAIL_USERNAME, Config.MAIL_PASSWORD]):
            print(f"\n--- [SIMULACAO] Email de resposta Tuna enviado para {email_destino} ---")
            print(f"Nome: {nome} | Novo Estado: {estado}\n")
            return True

        msg = MIMEMultipart('alternative')
        msg['From'] = f"Tuna Académica ISPGAYA <{Config.MAIL_DEFAULT_SENDER}>"
        msg['To'] = email_destino
        msg['Subject'] = f"A tua inscrição na Tuna Académica"

        if estado == "Aceite":
            texto_decisao = "Parabéns! Foste <strong>aceite</strong> na Tuna Académica. Em breve receberás mais informações sobre o horário dos ensaios."
            cor_decisao = "#059669"
        else:
            texto_decisao = "Lamentamos, mas neste momento a tua inscrição foi <strong>recusada/em espera</strong>. As vagas podem estar cheias, mas guardaremos o teu contacto para o futuro."
            cor_decisao = "#dc2626"

        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;color:#333;">
    <div style="background:#f97316;padding:20px 24px;border-radius:4px 4px 0 0;">
        <h1 style="margin:0;font-size:20px;color:#fff;">Tuna Académica</h1>
    </div>

    <div style="background:#fff;border:1px solid #eee;border-top:0;padding:24px;border-radius:0 0 4px 4px;">
        <p style="margin:0 0 16px;font-size:14px;">
            Olá <strong>{nome}</strong>,
        </p>
        <p style="margin:0 0 16px;font-size:14px;color:{cor_decisao};">
            {texto_decisao}
        </p>
        <p style="font-size:12px;color:#666;margin:0;">
            Obrigado pelo teu interesse no Laboratório Cultural.
        </p>
    </div>
</div>
"""
        msg.attach(MIMEText(html_body, 'html'))

        try:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao enviar e-mail de resposta tuna: {e}")
            return False
