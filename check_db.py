import os
import sys
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lab_cultural_flask'))

from lab_cultural_flask.app import create_app, get_db

import json

app = create_app()
with app.app_context():
    db = get_db()
with app.app_context():
    db = get_db()
    with db.cursor() as cursor:
        for table in ['inscricoes_eventos', 'inscricoes_teatro']:
            cursor.execute(f"DESCRIBE {table}")
            print(f"Columns for {table}:", cursor.fetchall())


