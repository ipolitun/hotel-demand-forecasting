from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig

class ScriptsSettings(ConfigBase):
    database: DatabaseConfig = DatabaseConfig()

scripts_settings = ScriptsSettings()
