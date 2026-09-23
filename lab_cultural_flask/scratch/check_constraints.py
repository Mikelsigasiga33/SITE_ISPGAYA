
import pymysql
from config import Config

def check_constraints():
    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        port=Config.MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = 'livros' AND TABLE_SCHEMA = 'lab_cultural' AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            constraints = cursor.fetchall()
            print("Constraints for 'livros' table:")
            for c in constraints:
                print(f"- {c['COLUMN_NAME']} -> {c['REFERENCED_TABLE_NAME']}.{c['REFERENCED_COLUMN_NAME']} ({c['CONSTRAINT_NAME']})")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    check_constraints()
