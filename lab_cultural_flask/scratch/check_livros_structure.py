import sqlite3
import os

db_path = 'lab_cultural.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livros LIMIT 1")
    row = cursor.fetchone()
    if row:
        print("Livros table structure:")
        print(dict(row).keys())
    else:
        # If table is empty, get column info
        cursor.execute("PRAGMA table_info(livros)")
        columns = cursor.fetchall()
        print("Livros table columns:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
    conn.close()
else:
    print("Database not found.")
