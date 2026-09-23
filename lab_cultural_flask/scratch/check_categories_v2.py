import sqlite3
import os
import sys

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = 'lab_cultural.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM categorias")
    rows = cursor.fetchall()
    print("Categories:")
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}")
    conn.close()
else:
    print("Database not found.")
