"""密码哈希与 JWT 签发/校验。"""

from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

PBKDF2_ITERATIONS = 120_000
TOKEN_TYPE = "bearer"


def hash_password(password: str, salt: str | None = None) -> str:
    """PBKDF2-SHA256 哈希，格式 pbkdf2$<salt>$<hex>。"""
    import hashlib
    import secrets

    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """常量时间比较哈希，防止时序侧信道。"""
    import hashlib
    import hmac

    try:
        scheme, salt, digest = stored.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(candidate.hex(), digest)


def create_access_token(user_id: int, username: str, role: str) -> str:
    """签发带 sub/username/role 与 exp 的 HS256 JWT。"""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """校验签名与过期时间，返回 JWT payload。"""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
