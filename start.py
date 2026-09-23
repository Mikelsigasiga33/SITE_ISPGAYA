#!/usr/bin/env python3
"""
Script para executar o Laboratório Cultural Flask
"""

import os
import sys

# Adicionar o diretório do projeto ao PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lab_cultural_flask'))

# Agora importar e executar a aplicação
from lab_cultural_flask.app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)