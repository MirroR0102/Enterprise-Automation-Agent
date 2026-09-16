"""周报 API：列表与单条详情查询。"""

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
    """分页列出当前用户的已保存周报。"""
    items = user_store.list_weekly_reports(user.id, limit=limit)
    return {"items": items}


@router.get("/reports/{report_id}")
def get_report(report_id: int, user: User = Depends(get_current_user)) -> dict:
    """按 ID 获取周报详情；不存在则 404。"""
    row = user_store.get_weekly_report(user.id, report_id)
    if row is None:
        raise HTTPException(status_code=404, detail="周报不存在")
    return row
