"""FastAPI 应用入口：路由注册、CORS、静态前端与健康检查。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.logs import router as logs_router
from app.api.reports import router as reports_router
from app.config import ROOT_DIR
from app.db.mysql import init_schema_and_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """启动时初始化数据库表结构与演示账号。"""
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
app.include_router(reports_router)


@app.get("/api/health")
def health() -> dict:
    """存活探针。"""
    return {"ok": True}


# 若存在 web/ 目录则挂载 SPA 静态资源
web_dir = Path(ROOT_DIR / "web")
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
