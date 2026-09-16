"""FastAPI 鉴权依赖：从 Bearer JWT 解析当前用户与角色校验。"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.auth.models import User
from app.auth.security import decode_access_token
from app.db.mysql import fetch_user_by_id

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    """解析 Authorization 头中的 JWT，加载数据库用户；无效则 401。"""
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_access_token(creds.credentials)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
        ) from exc
    row = fetch_user_by_id(user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return User(
        id=int(row["id"]),
        username=row["username"],
        role=row["role"],
        password_hash=row.get("password_hash", ""),
    )


def require_role(*roles: str):
    """工厂：生成要求指定角色的 Depends，权限不足返回 403。"""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user

    return dependency
