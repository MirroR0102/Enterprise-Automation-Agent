from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    role: str
    password_hash: str = ""
