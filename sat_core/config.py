import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "SWAGGER_API"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "0000"),
}

SWAGGER_FILE = os.environ.get("SWAGGER_FILE", r"swagger.json")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

GOOGLE_GENAI_API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY", "AIzaSyA-_S-6bLg--uX_VSK_zqEyxNSyak2WS30")


