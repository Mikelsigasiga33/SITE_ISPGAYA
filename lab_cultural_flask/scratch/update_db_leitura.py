import pymysql

db = pymysql.connect(host='localhost', user='root', password='', database='lab_cultural', port=3307)
cursor = db.cursor()
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membros_leitura (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(200) NOT NULL,
        email VARCHAR(200) NOT NULL,
        estado ENUM('Pendente', 'Aceite', 'Recusado') DEFAULT 'Pendente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db.commit()
    print("Table membros_leitura created")
except Exception as e:
    print("Error:", e)
