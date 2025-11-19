from jose import jwt
from datetime import datetime, timedelta, timezone
from auth_service.config import auth_config


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=auth_config.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, auth_config.secret_key, algorithm=auth_config.algorithm)
    return encode_jwt
