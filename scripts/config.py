from pydantic import Field

from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig


class ScriptsSettings(ConfigBase):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


scripts_settings = ScriptsSettings()
