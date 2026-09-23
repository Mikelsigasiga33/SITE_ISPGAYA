import sqlite3

conn = sqlite3.connect('lab_cultural.db')
cursor = conn.cursor()

# Remove the time part from publicado_em where length is > 10
cursor.execute('''
    UPDATE noticias 
    SET publicado_em = substr(publicado_em, 1, 10) 
    WHERE length(publicado_em) > 10
''')

conn.commit()
conn.close()
print('Dates fixed!')
