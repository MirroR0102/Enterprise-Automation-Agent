from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.deps import get_current_user
from app.auth.models import User
from app.db import user_store

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports")
def list_reports(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
) -> dict:
    items = user_store.list_weekly_reports(user.id, limit=limit)
    return {"items": items}


@router.get("/reports/{report_id}")
def get_report(report_id: int, user: User = Depends(get_current_user)) -> dict:
    row = user_store.get_weekly_report(user.id, report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="周报不存在")
    return row
