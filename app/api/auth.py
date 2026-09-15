from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.deps import get_current_user
from app.auth.models import User
from app.auth.security import TOKEN_TYPE, create_access_token, verify_password
from app.db.mysql import fetch_user_by_username
from fastapi import Depends

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


@router.post("/login")
def login(body: LoginBody) -> dict:
    row = fetch_user_by_username(body.username)
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token(int(row["id"]), row["username"], row["role"])
    return {"access_token": token, "token_type": TOKEN_TYPE, "role": row["role"]}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "username": user.username, "role": user.role}
