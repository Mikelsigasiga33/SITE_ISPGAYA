import os
import sys

# Adicionar o diretório raiz ao sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from lab_cultural_flask.app import create_app

app = create_app()



