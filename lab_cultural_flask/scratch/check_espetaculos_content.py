import sqlite3
import os

db_path = 'lab_cultural.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM espetaculos")
    rows = cursor.fetchall()
    print("Espetaculos current content:")
    for row in rows:
        print(dict(row))
    conn.close()
else:
    print("Database not found.")
