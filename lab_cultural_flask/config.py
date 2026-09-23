import os


class Config:
    # Chave secreta para sessões
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ispgaya_lab_cultural_secret_2025')

    # Pepper para Hashing de Passwords (camada de segurança adicional)
    PEPPER = os.environ.get('DB_PEPPER', 'ispgaya_cultural_pepper_secret_2026_key!')

    # Configuração de Base de Dados
    DB_TYPE = 'sqlite'  # 'mysql' ou 'sqlite'
    
    # Configuração SQLite
    SQLITE_DB = os.path.join(os.path.dirname(__file__), 'lab_cultural.db')

    # Configuração MySQL (XAMPP) - Mantida para referência
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # sem password no XAMPP por defeito
    MYSQL_DB = 'lab_cultural'
    MYSQL_PORT = 3307

    # Upload de imagens (opcional)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB máximo
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Paginação
    ITEMS_PER_PAGE = 9

    # Configuração de E-mail (SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'bilheteira.labcultural@gmail.com'
    MAIL_PASSWORD = 'lwhqvusseymszjyz' 
    MAIL_DEFAULT_SENDER = 'bilheteira.labcultural@gmail.com'

    # Configuração da API do Gemini para o Chatbot Inteligente
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyALbYQzNMkskJfE-bNb0LYxXj3tmx4MJ1E')
