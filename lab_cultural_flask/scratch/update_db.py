import pymysql

db = pymysql.connect(host='localhost', user='root', password='', database='lab_cultural', port=3307)
cursor = db.cursor()
try:
    cursor.execute("ALTER TABLE membros_teatro ADD COLUMN estado ENUM('Pendente', 'Aceite', 'Recusado') DEFAULT 'Pendente'")
    db.commit()
    print("Column added")
except Exception as e:
    print("Error or already exists:", e)
