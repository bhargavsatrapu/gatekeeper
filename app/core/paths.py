from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
UI_DIR = BASE_DIR / "ui"
UPLOADS_DIR = BASE_DIR / "uploads"


def ensure_directories_exist() -> None:
    UI_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


