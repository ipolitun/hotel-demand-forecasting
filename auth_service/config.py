from pydantic import field_validator, Field
from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig


class AuthServiceConfig(ConfigBase):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    secret_key: str
    algorithm: str = "HS256"
    scheduler_key: str
    access_token_expire_minutes: int = 60

    @field_validator("scheduler_key", mode="before")
    def ensure_scheduler_key(cls, v):
        if not v:
            raise ValueError("SCHEDULER_KEY is required for auth_service")
        return v


auth_config = AuthServiceConfig()
