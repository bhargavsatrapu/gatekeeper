# GATEKEEPER – Project Structure and Responsibilities

This document describes the modular layout, responsibilities, endpoints, and how to run/extend the app.

## Directory Layout

```
GATEKEEPER/
├─ app/                      # FastAPI backend
│  ├─ main.py                # App wiring: routers, static mounts, DB pool lifecycle
│  ├─ core/
│  │  ├─ config.py           # Environment-based settings
│  │  └─ paths.py            # Resolved dirs; ensures `ui/` and `uploads/`
│  ├─ db/
│  │  └─ pool.py             # psycopg2 connection pool helpers
│  ├─ routers/
│  │  ├─ files.py            # UI root, upload, files list/download/delete, summary
│  │  └─ apis.py             # Ingest spec to DB, list ingested APIs
│  ├─ repositories/
│  │  └─ api_specs.py        # DDL + insert logic for `api_specs`
│  └─ utils/
│     └─ files.py            # Shared helpers (safe path checks)
│
├─ ui/                       # Static web UI served at /ui
│  ├─ index.html             # Dashboard (upload, list, viewer, API checkbox list)
│  └─ viewer.html            # Swagger UI (renders ?url=/uploads/<file>)
│
├─ uploads/                  # Uploaded specs (.json/.yaml/.yml), exposed at /uploads
│
├─ docs/
│  └─ PROJECT_STRUCTURE.md   # This document
│
├─ requirements.txt          # Python dependencies
└─ README.md                 # Quick start
```

## Responsibilities

### app/main.py
- Creates FastAPI app.
- Startup: `ensure_directories_exist()` and init DB pool.
- Shutdown: close DB pool.
- Mounts static: `/ui` → `ui/`, `/uploads` → `uploads/`.
- Includes routers: `files`, `apis`.

### app/core/
- `config.py`: Reads env vars: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- `paths.py`: Central path helpers; ensures required directories exist.

### app/db/
- `pool.py`: `init_pool()`, `close_pool()`, `get_conn()`, `put_conn()` (psycopg2 pool).

### app/routers/
- `files.py`:
  - `GET /` → serve `ui/index.html`.
  - `POST /upload` → upload and store file under `uploads/`.
  - `GET /files` → list uploaded files.
  - `GET /files/{filename}` → download file.
  - `DELETE /files/{filename}` → delete file.
  - `GET /files/{filename}/summary` → summarize OpenAPI.
- `apis.py`:
  - `POST /files/{filename}/ingest` → parse spec, resolve `$ref`s, insert operations into DB.
  - `GET /apis` → return list of ingested APIs (id, method, path, summary).

### app/repositories/
- `api_specs.py`: `ensure_table(cur)` and `insert_operations(swagger, cur)`.

### app/utils/
- `files.py`: `safe_uploaded_path(filename)` protects against path traversal.

### ui/
- `index.html`: Drag-drop upload, file list with actions, viewer iframe, summary panel, API checkbox list loaded from `/apis`.
- `viewer.html`: Swagger UI rendering a spec from `?url`.

## Endpoints
- UI Root: `GET /`
- File operations: `POST /upload`, `GET /files`, `GET /files/{filename}`, `DELETE /files/{filename}`, `GET /files/{filename}/summary`
- Ingestion/APIs: `POST /files/{filename}/ingest`, `GET /apis`
- Static mounts: `/ui`, `/uploads`

## Configuration
PowerShell example:
```powershell
$env:DB_NAME="gatekeeper"; $env:DB_USER="postgres"; $env:DB_PASSWORD=""; $env:DB_HOST="localhost"; $env:DB_PORT="5432"
```

## Run
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- UI: http://127.0.0.1:8000/
- Docs: http://127.0.0.1:8000/docs

## Extend
- New routes: add under `app/routers/` and include via `app/main.py`.
- New DB entities: create repo in `app/repositories/` and use `app/db/pool.py`.
- UI additions: add files under `ui/`.
