from pydantic_settings import SettingsConfigDict

from shared.base_config import ConfigBase


class DatabaseConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="DB_")

    user: str
    password: str
    host: str = "db"
    port: int = 5432
    name: str

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


database_config = DatabaseConfig()
