import sqlite3
import os
from datetime import datetime, timedelta

def run():
    db_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\lab_cultural.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Identificar itens não relacionados com teatro em 'espetaculos'
    # Categorias: 1: Música, 2: Teatro, 3: Literatura, 4: Arte, 5: Cinema
    migration_map = {
        3: {'cat': 5, 'tipo': 'interno'}, # Os Lusíadas
        4: {'cat': 1, 'tipo': 'interno'}, # Noite de Fados
        5: {'cat': 1, 'tipo': 'interno'}, # Concerto de Natal
        6: {'cat': 5, 'tipo': 'interno'}, # Festival de Curtas
        7: {'cat': 4, 'tipo': 'interno'}, # Workshop Pintura
        9: {'cat': 4, 'tipo': 'interno'}, # Gala
        10: {'cat': 1, 'tipo': 'interno'} # Tunas
    }

    print("--- INICIANDO MIGRAÇÃO ---")
    for esp_id, meta in migration_map.items():
        cursor.execute("SELECT * FROM espetaculos WHERE id = ?", (esp_id,))
        esp = cursor.fetchone()
        if esp:
            # Mapear entrada do teatro para tipo_ingresso do evento
            tipo_ingresso = 'gratis'
            if esp['entrada'] == 'pago':
                tipo_ingresso = 'pago'
            
            # Garantir caminho da imagem correto
            imagem = esp['imagem']
            if imagem and not imagem.startswith('img/'):
                imagem = f"img/teatro/{imagem}"

            # Mover para eventos
            cursor.execute("""
                INSERT INTO eventos (titulo, descricao, data_evento, hora, local_id, tipo, categoria_id, destaque, imagem, tipo_ingresso, preco, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                esp['titulo'],
                esp['descricao'],
                esp['data_evento'],
                esp['hora'],
                1, # Auditório ISPGAYA
                meta['tipo'],
                meta['cat'],
                esp['destaque'],
                imagem,
                tipo_ingresso,
                esp['preco'] or 0.00
            ))
            # Desativar em espetaculos
            cursor.execute("UPDATE espetaculos SET ativo = 0 WHERE id = ?", (esp_id,))
            print(f"Movido: ID {esp_id} ('{esp['titulo']}') -> Programação Cultural (Eventos).")

    # 2. Adicionar novos itens específicos de Teatro
    today = datetime.now()
    new_teatros = [
        {
            'titulo': 'Falar Verdade a Ler (Almeida Garrett)',
            'descricao': 'Uma das comédias mais emblemáticas do teatro português. O Clube de Teatro ISPGAYA explora as peripécias de uma sociedade onde a mentira é moeda de troca, mas o amor procura a verdade.',
            'tipo': 'espetaculo',
            'data': (today + timedelta(days=25)).strftime('%Y-%m-%d'),
            'hora': '21:30',
            'imagem': 'img/teatro/espetaculo_1.jpg',
            'entrada': 'gratuita'
        },
        {
            'titulo': 'À Espera de Godot (Samuel Beckett)',
            'descricao': 'Uma interpretação contemporânea da obra-prima do teatro do absurdo. No palco, dois personagens aguardam por Godot, numa reflexão profunda sobre o tempo, a esperança e a existência humana.',
            'tipo': 'espetaculo',
            'data': (today + timedelta(days=40)).strftime('%Y-%m-%d'),
            'hora': '21:00',
            'imagem': 'img/teatro/espetaculo_4.jpg',
            'entrada': 'pago',
            'preco': 3.50
        },
        {
            'titulo': 'Ensaio Aberto: O Marinheiro',
            'descricao': 'Acompanha o processo de ensaio da peça estática de Fernando Pessoa. Uma oportunidade única para ver os bastidores e o trabalho de encenação do nosso grupo.',
            'tipo': 'ensaio',
            'data': (today + timedelta(days=12)).strftime('%Y-%m-%d'),
            'hora': '18:30',
            'imagem': 'img/teatro/espetaculo_2_2.jpg',
            'entrada': 'gratuita'
        },
        {
            'titulo': 'Workshop: Presença de Palco e Dicção',
            'descricao': 'Workshop prático focado em técnicas de respiração, projeção vocal e postura corporal, essencial para atores e para quem deseja melhorar a sua comunicação pública.',
            'tipo': 'workshop',
            'data': (today + timedelta(days=18)).strftime('%Y-%m-%d'),
            'hora': '14:00',
            'imagem': 'img/teatro/espetaculo_2_3.jpg',
            'entrada': 'gratuita'
        },
        {
            'titulo': 'Auto da Compadecida: Adaptação Livre',
            'descricao': 'Uma explosão de cores e humor nordestino no Auditório ISPGAYA. A esperteza de João Grilo e Chicó posta à prova no julgamento final.',
            'tipo': 'espetaculo',
            'data': (today + timedelta(days=55)).strftime('%Y-%m-%d'),
            'hora': '21:30',
            'imagem': 'img/teatro/espetaculo_7.jpg',
            'entrada': 'gratuita'
        },
        {
            'titulo': 'Workshop: Cenografia e Adereços',
            'descricao': 'Aprende a transformar materiais simples em elementos de cena impactantes. Sessão prática com o apoio da equipa técnica do Clube de Teatro.',
            'tipo': 'workshop',
            'data': (today + timedelta(days=32)).strftime('%Y-%m-%d'),
            'hora': '10:30',
            'imagem': 'img/teatro/espetaculo_2_4.jpg',
            'entrada': 'gratuita'
        }
    ]

    print("\n--- ADICIONANDO NOVO CONTEÚDO DE TEATRO ---")
    for t in new_teatros:
        cursor.execute("""
            INSERT INTO espetaculos (titulo, descricao, tipo, data_evento, hora, imagem, entrada, preco, ativo, destaque, categoria_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 2)
        """, (
            t['titulo'], t['descricao'], t['tipo'], t['data'], t['hora'], t['imagem'], t['entrada'], t.get('preco', 0.00)
        ))
        print(f"Adicionado: {t['titulo']} ({t['tipo']})")

    conn.commit()
    conn.close()
    print("\n--- PROCESSO CONCLUÍDO COM SUCESSO ---")

if __name__ == '__main__':
    run()
