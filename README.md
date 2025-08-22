# GATEKEEPER - Swagger Upload UI + API

Simple FastAPI service with a minimal web UI to upload Swagger/OpenAPI documents (.json/.yaml/.yml). Files are saved to the `uploads/` directory.

## Setup (Windows PowerShell)

1. Create and activate venv (already created as `.venv`):

```powershell
 .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
 python -m pip install -r requirements.txt
```

3. Run the dev server:

```powershell
 uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Open the UI:

 - Home: `http://127.0.0.1:8000/`
 - API docs: `http://127.0.0.1:8000/docs`

## Notes

- Accepted file types: `.json`, `.yaml`, `.yml`
- Uploaded files are stored under `uploads/` at the project root.

