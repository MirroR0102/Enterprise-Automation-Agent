from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.logs import router as logs_router
from app.config import ROOT_DIR
from app.db.mysql import init_schema_and_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_schema_and_seed()
    yield


app = FastAPI(title="Enterprise Ops Agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(logs_router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


web_dir = Path(ROOT_DIR / "web")
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
