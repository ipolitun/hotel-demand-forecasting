import uuid
from datetime import datetime, timezone, timedelta

from jose import jwt, JWTError

from auth_service.config import auth_config
from auth_service.schemas.token import TokenAccessPayload, TokenRefreshPayload, TokenType


class JWTProvider:
    def create_access_token(self, payload: TokenAccessPayload) -> str:
        return self._encode_token(
            payload=payload,
            secret_key=auth_config.jwt_config.secret_key,
            lifetime_minutes=auth_config.access_token_expire_minutes,
            algorithm=auth_config.jwt_config.hash_algorithm,
        )

    def create_refresh_token(self, payload: TokenRefreshPayload) -> str:
        return self._encode_token(
            payload=payload,
            secret_key=auth_config.jwt_config.secret_key,
            lifetime_minutes=auth_config.refresh_token_expire_minutes,
            algorithm=auth_config.jwt_config.hash_algorithm,
        )

    @staticmethod
    def decode_token(
            token: str | None
    ) -> TokenAccessPayload | TokenRefreshPayload | None:
        if not token:
            return None

        try:
            decoded = jwt.decode(
                token,
                auth_config.jwt_config.secret_key,
                algorithms=[auth_config.jwt_config.hash_algorithm],
            )
            token_type = decoded.get("token_type")
            if token_type == TokenType.REFRESH:
                return TokenRefreshPayload(**decoded)
            return TokenAccessPayload(**decoded)

        except JWTError:
            return None

    @staticmethod
    def _encode_token(
            payload: TokenAccessPayload | TokenRefreshPayload,
            secret_key: str,
            lifetime_minutes: int,
            algorithm: str = auth_config.jwt_config.hash_algorithm,
    ) -> str:
        to_encode = payload.model_dump(exclude_none=True)
        expire = datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes)
        to_encode.update({"exp": expire})
        if isinstance(payload, TokenRefreshPayload):
            jti = str(uuid.uuid4())
            to_encode.update({"jti": jti})
        return jwt.encode(to_encode, secret_key, algorithm=algorithm)
