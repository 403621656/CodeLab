from pwdlib import PasswordHash

from core.config import settings


password_hash = PasswordHash.recommended()
local_token = settings.SECRET_KEY


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)
