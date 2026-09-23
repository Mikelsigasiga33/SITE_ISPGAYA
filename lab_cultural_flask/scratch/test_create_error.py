from app import get_db, create_app
from app.models.evento import Evento

app = create_app()
with app.app_context():
    dados = {
        'titulo': 'Evento Teste Erro',
        'descricao': 'Descricao teste',
        'data_evento': '2026-05-20',
        'hora': '20:00',
        'tipo': 'interno',
        'cidade': 'Vila Nova de Gaia',
        'tipo_ingresso': 'gratis'
    }
    
    print("Tentando criar evento...")
    try:
        if Evento.criar(dados):
            print("Sucesso!")
        else:
            print("Falhou (retornou False)")
    except Exception as e:
        print(f"Exceção capturada: {e}")
