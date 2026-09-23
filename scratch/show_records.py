import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lab_cultural_flask', 'lab_cultural.db')
email = 'ispg2023103434@ispgaya.pt'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    cursor.execute(f"PRAGMA table_info({table});")
    columns = [row[1] for row in cursor.fetchall()]
    
    for col in columns:
        try:
            cursor.execute(f"SELECT * FROM {table} WHERE {col} = ?", (email,))
            rows = cursor.fetchall()
            if rows:
                print(f"\n--- Table: {table} (column: {col}) ---")
                print("Columns:", columns)
                for row in rows:
                    print(row)
        except sqlite3.OperationalError:
            pass

conn.close()
