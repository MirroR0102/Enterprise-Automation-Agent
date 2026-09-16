"""运维日志 API：仅 dev 角色可查询 agent_logs。"""

from fastapi import APIRouter, Depends, Query

from app.auth.deps import require_role
from app.auth.models import User
from app.logging_service import list_recent

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs")
def get_logs(
    session_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(require_role("dev")),
) -> dict:
    """查询最近日志，可按 session_id 过滤。"""
    return {"items": list_recent(limit=limit, session_id=session_id), "viewer": user.username}
