import os

path = 'templates/lab_cultural/noticias.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('Eventos — ISPGAYA', 'Notícias — ISPGAYA')
c = c.replace('Programação Cultural', 'Notícias')
c = c.replace('A nossa agenda pretende contribuir para o desenvolvimento pessoal e cultural. Fica a conhecer os eventos e participa connosco.', 'Acompanhe as últimas novidades, anúncios e atividades da nossa comunidade.')
c = c.replace('Procurar evento...', 'Procurar notícia...')
c = c.replace('Sem eventos disponíveis', 'Sem notícias disponíveis')
c = c.replace('Sem eventos para estes filtros', 'Sem notícias para estes filtros')
c = c.replace('evento_detalhe', 'noticia_detalhe')
c = c.replace('evento_id', 'noticia_id')
c = c.replace('eventos', 'noticias')
c = c.replace('evento', 'noticia')
c = c.replace('Evento', 'Notícia')
c = c.replace('noticia.data_noticia', 'noticia.publicado_em')
c = c.replace('data_noticia', 'publicado_em')
c = c.replace('Notícia.get_all', 'Noticia.get_all')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('Feito!')
