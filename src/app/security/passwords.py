from functools import lru_cache
from passlib.context import CryptContext
from passlib.exc import MissingBackendError
import hashlib
from ..config import get_settings

@lru_cache()
def _pwd_context() -> CryptContext:
    scheme = get_settings().password_hashing_scheme.lower()
    if scheme == "argon2":
        return CryptContext(schemes=["argon2"], deprecated="auto")
    elif scheme in {"bcrypt", "bcrypt_sha256"}:
        return CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
    return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

@lru_cache()
def _fallback_context() -> CryptContext:
    return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def _simple_hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def hash_password(pw: str) -> str:
    try:
        return _pwd_context().hash(pw)
    except Exception:
        try:
            return _fallback_context().hash(pw)
        except Exception:
            return _simple_hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return _pwd_context().verify(pw, hashed)
    except Exception:
        try:
            return _fallback_context().verify(pw, hashed)
        except Exception:
            return _simple_hash(pw) == hashed
