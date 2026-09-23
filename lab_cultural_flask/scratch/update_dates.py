import sqlite3
conn = sqlite3.connect('lab_cultural.db')
cursor = conn.cursor()
cursor.execute("UPDATE eventos SET data_evento = '2026-08-01' WHERE id = 1")
cursor.execute("UPDATE eventos SET data_evento = '2026-08-15' WHERE id = 2")
cursor.execute("UPDATE eventos SET data_evento = '2026-09-01' WHERE id = 3")
conn.commit()
conn.close()
print("Dates updated.")
