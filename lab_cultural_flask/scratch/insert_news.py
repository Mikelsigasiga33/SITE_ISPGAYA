import sqlite3
from datetime import datetime

conn = sqlite3.connect('lab_cultural.db')
cursor = conn.cursor()

novas_noticias = [
    ('Nova Peça do Clube de Teatro: "Sombras do Passado"', 
     'O Clube de Teatro do ISPGAYA anuncia a sua mais recente produção, prometendo uma viagem inesquecível pelo drama clássico com um toque contemporâneo.', 
     'É com enorme entusiasmo que o Clube de Teatro do ISPGAYA apresenta a sua nova peça, "Sombras do Passado". Após meses de ensaios intensos e preparação dedicada, os nossos alunos sobem ao palco no próximo mês.\n\nA peça explora temas intemporais como a memória, a identidade e os laços familiares que nos unem e, por vezes, nos separam. Com um elenco talentoso composto exclusivamente por estudantes da nossa instituição, esta produção marca também a estreia de um novo sistema de iluminação no auditório principal.\n\n"Trabalhámos muito para trazer uma visão fresca a um texto tão denso", afirma o encenador principal. Todos os alunos, docentes e comunidade local estão convidados a assistir. Os bilhetes estarão brevemente disponíveis na secretaria do Lab Cultural.', 
     2, '2026-06-15 10:30:00', 1, 'photo-1507676184212-d0330a151280'),

    ('Tuna Feminina do ISPGAYA Vence Prémio Melhor Passacalles', 
     'A nossa Tuna viajou até ao sul do país e trouxe para casa o prémio de Melhor Passacalles num dos maiores festivais do ano.', 
     'O último fim de semana foi de celebração e muita música para a Tuna do ISPGAYA. Na sua participação no Festival Académico do Sul, a nossa tuna destacou-se pela sua alegria, musicalidade e interação com o público.\n\nO momento alto da participação foi a conquista do prémio de "Melhor Passacalles", uma categoria altamente disputada que avalia a animação de rua, o trajo, a criatividade e a capacidade de envolver os transeuntes.\n\n"Foi uma experiência incrível. Sentimos o apoio de todos e conseguimos mostrar o verdadeiro espírito académico do ISPGAYA", partilhou a Magister. A tuna prepara agora a sua próxima atuação, que terá lugar na cerimónia de encerramento do semestre.', 
     1, '2026-06-10 14:00:00', 1, 'photo-1514320291840-2e0a9bf2a9ae'),

    ('Sessão do Clube de Leitura: Especial Autores Portugueses Contemporâneos', 
     'A próxima sessão do Clube de Leitura será inteiramente dedicada à nova vaga de escritores de língua portuguesa.', 
     'Amantes dos livros, preparem-se! O Clube de Leitura do ISPGAYA tem o prazer de anunciar que a sessão deste mês focará exclusivamente em autores portugueses contemporâneos.\n\nVamos debater obras recentes que têm agitado o panorama literário nacional, explorando novas narrativas, estilos experimentais e as vozes emergentes da nossa cultura. Como sempre, a participação é gratuita e aberta a todos os alunos, mesmo aqueles que não tenham lido as obras na íntegra, mas que queiram ouvir e partilhar perspetivas.\n\nO encontro será acompanhado de chá e bolinhos na biblioteca principal. Tragam as vossas sugestões para os próximos meses e juntem-se a nós nesta partilha literária.', 
     3, '2026-06-05 09:15:00', 0, 'photo-1481627834876-b7833e8f5570'),

    ('Exposição Anual de Artes Plásticas: "Mundos Paralelos"', 
     'Os trabalhos desenvolvidos pelos alunos ao longo do ano vão estar em exposição na galeria principal do campus.', 
     'O Lab Cultural convida toda a comunidade académica a visitar a exposição "Mundos Paralelos", uma mostra impressionante dos trabalhos finais dos alunos dos cursos criativos.\n\nA exposição reúne dezenas de obras que vão desde a pintura tradicional e escultura até instalações interativas e arte digital. O tema deste ano desafiou os estudantes a explorarem perspetivas alternativas e realidades divergentes, resultando numa coleção diversificada e visualmente estimulante.\n\nA inauguração oficial acontece na próxima sexta-feira ao final da tarde e contará com a presença dos jovens artistas, que estarão disponíveis para falar sobre os seus processos criativos. Não percam!', 
     4, '2026-05-28 11:45:00', 1, 'photo-1460661419201-fd4cecdf8a8b')
]

for n in novas_noticias:
    cursor.execute('''
        INSERT INTO noticias (titulo, resumo, conteudo, categoria_id, publicado_em, destaque, imagem, ativo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', n)

conn.commit()
conn.close()
print('Notícias inseridas com sucesso!')
