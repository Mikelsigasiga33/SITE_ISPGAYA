
import pymysql

db = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='lab_cultural',
    port=3307,
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with db.cursor() as cursor:
        cursor.execute("DESCRIBE espetaculos")
        columns = cursor.fetchall()
        print("\nColumns in 'espetaculos':")
        for col in columns:
            print(f"- {col['Field']} ({col['Type']})")
finally:
    db.close()
