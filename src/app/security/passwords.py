from passlib.context import CryptContext

from ..config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=[settings.password_hashing_scheme], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)
