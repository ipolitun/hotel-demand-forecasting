from passlib.context import CryptContext

from auth_service.config import auth_config

pwd_context = CryptContext(schemes=[auth_config.password_hash_algorithm], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
