import sqlite3
import os
import shutil

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lab_cultural_flask', 'lab_cultural.db')
BACKUP_PATH = DB_PATH + '.bak'
email = 'ispg2023103434@ispgaya.pt'

# Create a backup
if os.path.exists(DB_PATH):
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup created at: {BACKUP_PATH}")
else:
    print("Error: Database file not found!")
    exit(1)

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
            # Check how many would be deleted
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = ?", (email,))
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.execute(f"DELETE FROM {table} WHERE {col} = ?", (email,))
                print(f"Deleted {count} rows from table '{table}', column '{col}'")
        except sqlite3.OperationalError as e:
            print(f"Error checking/deleting from {table}.{col}: {e}")

conn.commit()
conn.close()
print("All deletions committed successfully.")
