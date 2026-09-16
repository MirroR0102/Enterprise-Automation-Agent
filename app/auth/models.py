"""鉴权领域模型。"""

from dataclasses import dataclass


@dataclass
class User:
    """已认证用户；password_hash 仅内部校验用，不对外暴露。"""

    id: int
    username: str
    role: str
    password_hash: str = ""
