import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.core.paths import UI_DIR, UPLOADS_DIR


router = APIRouter()


@router.get("/")
async def root() -> FileResponse:
    index_path = UI_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="UI not found. Missing ui/index.html")
    return FileResponse(str(index_path))


@router.post("/upload")
async def upload_swagger(file: UploadFile = File(...)) -> JSONResponse:
    allowed_extensions = {".json", ".yaml", ".yml"}
    extension = Path(file.filename).suffix.lower()
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload .json, .yaml, or .yml")

    destination = UPLOADS_DIR / file.filename
    counter = 1
    while destination.exists():
        destination = UPLOADS_DIR / f"{Path(file.filename).stem}_{counter}{extension}"
        counter += 1

    contents = await file.read()
    try:
        with open(destination, "wb") as f:
            f.write(contents)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    return JSONResponse(
        {
            "filename": destination.name,
            "originalFilename": file.filename,
            "sizeBytes": len(contents),
            "contentType": file.content_type,
            "message": "Upload successful",
            "url": f"/uploads/{destination.name}",
        }
    )


