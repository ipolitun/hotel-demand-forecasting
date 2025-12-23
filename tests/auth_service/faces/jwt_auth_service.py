from typing import Any


class FakeJWTAuthService:
    def __init__(self):
        self.revoked: list[tuple[str, str]] = []
        self.revoked_all: list[str] = []
        self._payloads: dict[str, Any] = {}

    def seed_refresh_payload(self, token: str, payload: Any) -> None:
        self._payloads[token] = payload

    @staticmethod
    async def generate_tokens(principal: Any) -> tuple[str, str]:
        return "access-token", "refresh-token"

    async def read_token(self, token: str) -> Any:
        return self._payloads.get(token)

    @staticmethod
    async def rotate_tokens(refresh_payload: Any, principal: Any) -> tuple[str, str]:
        return "access-token-2", "refresh-token-2"

    async def revoke_token(self, jti: str, user_id: str) -> None:
        self.revoked.append((jti, user_id))

    async def revoke_all_tokens(self, user_id: str) -> None:
        self.revoked_all.append(user_id)
