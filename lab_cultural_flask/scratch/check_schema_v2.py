import sqlite3
import os

db_path = 'lab_cultural.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("PRAGMA table_info(espetaculos)")
    for row in cursor.fetchall():
        print(row)
    conn.close()
else:
    print(f"File {db_path} not found")
