import sqlite3

conn = sqlite3.connect('lab_cultural.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info('noticias');")
for row in cursor.fetchall():
    print(row)
conn.close()
