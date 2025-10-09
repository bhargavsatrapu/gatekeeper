import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "SWAGGER_API"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "9496"),
}

SWAGGER_FILE = os.environ.get("SWAGGER_FILE", r"C:\Bhargav\SMALL_API\swagger.json")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")

GOOGLE_GENAI_API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY", "AIzaSyB3cm8W8O6U8498FbS1EXt5o8qHVe43yjc")


