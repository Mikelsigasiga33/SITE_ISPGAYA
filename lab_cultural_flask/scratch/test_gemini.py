import urllib.request
import urllib.error
import json

def obter_resposta_gemini(api_key, mensagem):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    system_instruction = (
        "És o Assistente Virtual do website Laboratório Cultural do ISPGAYA (Instituto Superior Politécnico Gaya).\n"
        "O teu objetivo é ajudar os utilizadores a esclarecer dúvidas sobre os nossos clubes (Teatro, Tuna Académica e Biblioteca/Leitura), eventos e requisição de livros.\n\n"
        "Informações sobre o Laboratório Cultural:\n"
        "1. Clube de Teatro:\n"
        "   - Oferece ensaios semanais, espetáculos e reservas de bilhetes online com mapa de sala interativo.\n"
        "   - Para inscrever-se no Clube de Teatro (como membro), o utilizador deve aceder a: /lab-cultural/clube-teatro/juntar\n"
        "   - Página principal do Teatro: /lab-cultural/clube-teatro\n"
        "   - Galeria do Teatro: /lab-cultural/clube-teatro/galeria\n\n"
        "2. Tuna Académica:\n"
        "   - Grupo musical e académico do ISPGAYA. Atua em eventos académicos e festivais.\n"
        "   - Para juntar-se à Tuna, aceder a: /lab-cultural/tuna/juntar\n"
        "   - Página da Tuna: /lab-cultural/tuna\n"
        "   - Galeria da Tuna: /lab-cultural/tuna/galeria\n\n"
        "3. Clube de Leitura e Biblioteca:\n"
        "   - Permite consultar e requisitar livros do catálogo do laboratório de forma 100% virtual.\n"
        "   - Para fazer parte do Clube de Leitura (receber novidades de debates e encontros), aceder a: /lab-cultural/clube-leitura/juntar\n"
        "   - Página da Biblioteca: /biblioteca\n\n"
        "4. Eventos e Agenda:\n"
        "   - Temos palestras, workshops e conferências.\n"
        "   - Página de Eventos: /eventos\n\n"
        "Regras importantes de resposta:\n"
        "- Responde em Português de Portugal de forma simpática, clara, concisa e profissional.\n"
        "- O utilizador pode cometer pequenos erros de digitação (ex: \"increver\" em vez de \"inscrever\", \"teatru\", \"tunaa\"), deves perceber a sua intenção e responder com naturalidade.\n"
        "- Nunca inventes informações que não constam acima. Se não souberes a resposta, aconselha o utilizador a deixar uma mensagem usando a opção \"Enviar Mensagem\" para falarmos com a equipa de suporte.\n"
        "- Devolve a tua resposta em formato de texto limpo (Markdown simples sem exagerar nos negritos)."
    )
    
    payload = {
        "system_instruction": {
            "parts": [
                {"text": system_instruction}
            ]
        },
        "contents": [
            {
                "parts": [
                    {"text": mensagem}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 2000
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        import ssl
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=8, context=context) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            print("FULL RESPONSE:", json.dumps(res_data, indent=2))
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    print("TEXT:", parts[0].get("text"))
                    return
            print("Response:", json.dumps(res_data, indent=2))
    except urllib.error.HTTPError as e:
        print("HTTP Error Code:", e.code)
        print("HTTP Error Body:", e.read().decode('utf-8'))
    except Exception as e:
        print("General Exception:", str(e))

obter_resposta_gemini("AIzaSyALbYQzNMkskJfE-bNb0LYxXj3tmx4MJ1E", "fala me do clube de teatro")
