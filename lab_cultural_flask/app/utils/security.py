import html
import re
from datetime import datetime


def sanitize(text: str) -> str:
    """Escapa caracteres HTML para prevenir XSS."""
    if text is None:
        return ''
    return html.escape(str(text).strip())


def validar_data(data_str: str) -> bool:
    """Valida se uma string está no formato YYYY-MM-DD."""
    if not data_str:
        return False
    try:
        datetime.strptime(data_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validar_hora(hora_str: str) -> bool:
    """Valida se uma string está no formato HH:MM."""
    if not hora_str:
        return True  # A hora é opcional
    try:
        datetime.strptime(hora_str, '%H:%M')
        return True
    except ValueError:
        return False


def validar_email(email: str) -> bool:
    """Valida formato básico de e-mail."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email or ''))


def validar_campos(dados: dict, obrigatorios: list) -> list:
    """
    Valida que os campos obrigatórios estão presentes e não estão vazios.
    Retorna lista de erros (vazia = sem erros).
    """
    erros = []
    for campo in obrigatorios:
        valor = dados.get(campo, '').strip()
        if not valor:
            erros.append(f'O campo "{campo}" é obrigatório.')
    return erros


def sanitizar_dict(dados: dict, campos: list) -> dict:
    """Sanitiza (escapa XSS) um conjunto de campos de um dicionário."""
    resultado = {}
    for campo in campos:
        resultado[campo] = sanitize(dados.get(campo, ''))
    return resultado


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Verifica se a extensão de um ficheiro é permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


# Lista de passwords proibidas (comum em ataques de dicionário e dados da instituição)
PASSWORDS_PROIBIDAS = {
    "123456", "12345678", "123456789", "12345", "1234567", "1234567890",
    "password", "password123", "admin", "admin123", "qwerty", "letmein", 
    "welcome", "abc123", "portugal", "portugal123", "ispgaya", "ispgaya123", 
    "gaya", "gaya123", "vilanovadegaia", "porto", "porto123", "lisboa",
    "clube", "teatro", "tuna", "biblioteca", "leitura", "cultural",
    "shadow", "dragon", "master", "monkey", "killer", "trustnoone",
    "football", "soccer", "jesus", "christ", "godisgood", "iloveyou"
}

# Padrões comuns ou sequências fracas
PADROES_FRACOS = [
    "123",
    "1234",
    "abcd",
    "abc",
    "qwerty",
    "admin",
    "password",
    "ispgaya",
    "portugal"
]

def avaliar_password(password):
    """
    Avalia a robustez de uma password com base em vários critérios de segurança.
    Retorna uma tupla (classificacao, pontuacao, problemas, contem_padrao_fraco, e_proibida).
    """
    if not password:
        return "Fraca", 0, ["A password está vazia"], False, False

    pontuacao = 0
    problemas = []
    e_proibida = False
    contem_padrao_fraco = False
    padroes_encontrados = []

    # 1. Verificar se está na lista de passwords proibidas
    if password.lower() in PASSWORDS_PROIBIDAS:
        e_proibida = True
        problemas.append("A password consta na lista de passwords proibidas comuns")

    # 2. Comprimento mínimo (atualizado para 10 caracteres)
    if len(password) >= 12:
        pontuacao += 2
    elif len(password) >= 10:
        pontuacao += 1
    else:
        problemas.append("A password tem menos de 10 caracteres (comprimento mínimo)")

    # 3. Letras minúsculas
    tem_minuscula = bool(re.search(r"[a-z]", password))
    if tem_minuscula:
        pontuacao += 1
    else:
        problemas.append("A password não contém letras minúsculas")

    # 4. Letras maiúsculas
    tem_maiuscula = bool(re.search(r"[A-Z]", password))
    if tem_maiuscula:
        pontuacao += 1
    else:
        problemas.append("A password não contém letras maiúsculas")

    # 5. Números
    tem_numero = bool(re.search(r"[0-9]", password))
    if tem_numero:
        pontuacao += 1
    else:
        problemas.append("A password não contém números")

    # 6. Símbolos (caracteres especiais)
    tem_simbolo = bool(re.search(r"[^a-zA-Z0-9\s]", password))
    if tem_simbolo:
        pontuacao += 1
    else:
        problemas.append("A password não contém símbolos/caracteres especiais")

    # 7. Presença de padrões fracos
    for padrao in PADROES_FRACOS:
        if padrao in password.lower():
            contem_padrao_fraco = True
            padroes_encontrados.append(padrao)
            
    if contem_padrao_fraco:
        pontuacao -= 1
        problemas.append(f"A password contém sequências ou padrões fracos: {', '.join(padroes_encontrados)}")

    # Garantir que a pontuação não fica abaixo de 0
    pontuacao = max(0, pontuacao)

    # Classificação final: exibe "Fraca" se for proibida, menor de 10 caracteres, ou se faltar algum dos 4 tipos de caracteres obrigatórios
    if e_proibida or len(password) < 10 or not (tem_minuscula and tem_maiuscula and tem_numero and tem_simbolo):
        classificacao = "Fraca"
    else:
        if pontuacao <= 2:
            classificacao = "Fraca"
        elif pontuacao <= 4:
            classificacao = "Média"
        elif pontuacao == 5:
            classificacao = "Forte"
        else:
            classificacao = "Muito forte"

    return classificacao, pontuacao, problemas, contem_padrao_fraco, e_proibida
