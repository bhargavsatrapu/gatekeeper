from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.paths import ensure_directories_exist, UI_DIR, UPLOADS_DIR
from app.db.pool import init_pool, close_pool
from app.routers import files as files_router
from app.routers import apis as apis_router


app = FastAPI(title="GATEKEEPER")


@app.on_event("startup")
def on_startup() -> None:
    ensure_directories_exist()
    try:
        init_pool()
    except Exception:
        # Allow app to start even if DB is unreachable
        pass


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_pool()


app.include_router(files_router.router)
app.include_router(apis_router.router)

app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


