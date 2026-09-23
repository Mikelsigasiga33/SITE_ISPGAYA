import sys
import os

# Adicionar o diretório do projeto ao sys.path para poder importar a app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, g
from app import create_app, get_db

app = create_app()

with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM categorias")
        categorias = cursor.fetchall()
        print(f"Categorias encontradas: {len(categorias)}")
        for cat in categorias:
            print(f"- {cat['nome']}")

    # Testar query com %s
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM eventos WHERE id = ?", (15,))
        ev = cursor.fetchone()
        if ev:
            print(f"Evento 15: {ev['titulo']}")
            print(f"Tipo de data_evento: {type(ev['data_evento'])}")
            print(f"Valor: {ev['data_evento']}")
        else:
            print("Evento 15 não encontrado.")

    # Testar query com CURDATE()
    with db.cursor() as cursor:
        try:
            cursor.execute("SELECT * FROM eventos WHERE data_evento >= CURDATE()")
            eventos = cursor.fetchall()
            print(f"Eventos futuros: {len(eventos)}")
        except Exception as e:
            print(f"Erro no CURDATE(): {e}")
