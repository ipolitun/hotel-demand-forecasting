from pydantic import Field

from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig


class DataInterfaceConfig(ConfigBase):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


data_interface_config = DataInterfaceConfig()