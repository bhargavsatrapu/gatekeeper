import json
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.core.paths import UPLOADS_DIR
from app.utils.files import safe_uploaded_path
from app.db.pool import get_conn, put_conn
from app.repositories.api_specs import ensure_table, insert_operations


router = APIRouter()


@router.get("/files")
async def list_files() -> JSONResponse:
    items: List[Dict[str, object]] = []
    for p in sorted(UPLOADS_DIR.glob("*")):
        if p.is_file():
            stat = p.stat()
            items.append(
                {
                    "filename": p.name,
                    "sizeBytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "url": f"/uploads/{p.name}",
                }
            )
    return JSONResponse({"files": items})


@router.get("/files/{filename}")
async def download_file(filename: str) -> FileResponse:
    fpath = safe_uploaded_path(filename)
    return FileResponse(str(fpath), filename=fpath.name, media_type="application/octet-stream")


@router.delete("/files/{filename}")
async def delete_file(filename: str) -> JSONResponse:
    fpath = safe_uploaded_path(filename)
    try:
        fpath.unlink(missing_ok=False)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {exc}")
    return JSONResponse({"message": "Deleted", "filename": filename})


@router.get("/files/{filename}/summary")
async def file_summary(filename: str) -> JSONResponse:
    fpath = safe_uploaded_path(filename)
    text = fpath.read_text(encoding="utf-8", errors="ignore")

    data: Optional[dict] = None
    try:
        if fpath.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            try:
                import yaml  # type: ignore
            except Exception:
                raise HTTPException(status_code=500, detail="YAML support not installed. Please add PyYAML.")
            data = yaml.safe_load(text) if text.strip() else {}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse specification: {exc}")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Specification is not a valid object")

    info = data.get("info", {}) or {}
    title = info.get("title") or ""
    version = info.get("version") or ""

    paths = data.get("paths", {}) or {}
    num_paths = len(paths)

    http_methods = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
    op_counts: Dict[str, int] = {m: 0 for m in http_methods}
    for _path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() in op_counts and isinstance(operation, dict):
                op_counts[method.lower()] += 1

    tags = data.get("tags", []) or []
    servers = data.get("servers", []) or []
    components = data.get("components", {}) or {}
    security_schemes = components.get("securitySchemes", {}) or {}

    summary = {
        "title": title,
        "version": version,
        "numPaths": num_paths,
        "operationCounts": op_counts,
        "numTags": len(tags),
        "numServers": len(servers),
        "numSecuritySchemes": len(security_schemes),
    }

    return JSONResponse(summary)


@router.post("/files/{filename}/ingest")
async def ingest_file_to_db(filename: str) -> JSONResponse:
    fpath = safe_uploaded_path(filename)
    text = fpath.read_text(encoding="utf-8", errors="ignore")

    try:
        if fpath.suffix.lower() == ".json":
            swagger = json.loads(text)
        else:
            import yaml  # type: ignore
            swagger = yaml.safe_load(text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse spec: {exc}")

    if not isinstance(swagger, dict):
        raise HTTPException(status_code=400, detail="Spec is not a valid object")

    conn = get_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        conn.commit()
        inserted = insert_operations(swagger, cur)
        conn.commit()
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)

    return JSONResponse({"message": "Ingestion complete", "inserted": inserted, "file": filename, "url": f"/uploads/{filename}"})


@router.get("/apis")
async def list_ingested_apis() -> JSONResponse:
    conn = get_conn()
    try:
        try:
            import psycopg2.extras  # type: ignore
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        except Exception:
            cur = conn.cursor()

        ensure_table(cur)
        conn.commit()
        cur.execute("SELECT id, method, path, COALESCE(summary, '') AS summary FROM api_specs ORDER BY path ASC, method ASC")
        rows = cur.fetchall()

        items: List[Dict[str, str]] = []
        for r in rows:
            if isinstance(r, dict):
                items.append({"id": str(r.get("id")), "method": str(r.get("method") or ""), "path": str(r.get("path") or ""), "summary": str(r.get("summary") or "")})
            else:
                rid, method, path, summary = r  # type: ignore
                items.append({"id": str(rid), "method": str(method or ""), "path": str(path or ""), "summary": str(summary or "")})
        return JSONResponse({"apis": items})
    finally:
        try:
            cur.close()
        finally:
            put_conn(conn)


