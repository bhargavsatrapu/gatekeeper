from pathlib import Path
from fastapi import HTTPException

from app.core.paths import UPLOADS_DIR


def safe_uploaded_path(filename: str) -> Path:
    """Prevent path traversal and ensure file exists within uploads dir."""
    safe_name = Path(filename).name
    candidate = UPLOADS_DIR / safe_name
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


