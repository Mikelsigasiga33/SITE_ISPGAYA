import sys
sys.path.append('.')
from app import create_app

app = create_app()
print("GEMINI_API_KEY in Flask Config:", repr(app.config.get("GEMINI_API_KEY")))
