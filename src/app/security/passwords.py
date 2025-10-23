from functools import lru_cache
from passlib.context import CryptContext
from ..config import get_settings

@lru_cache()
def _pwd_context() -> CryptContext:
    scheme = get_settings().password_hashing_scheme.lower()
    if scheme == "argon2":
        return CryptContext(schemes=["argon2"], deprecated="auto")
    elif scheme in {"bcrypt", "bcrypt_sha256"}:
        return CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
    return CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(pw: str) -> str: return _pwd_context().hash(pw)
def verify_password(pw: str, hashed: str) -> bool: return _pwd_context().verify(pw, hashed)
