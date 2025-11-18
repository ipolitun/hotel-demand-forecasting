from datetime import date

from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig


class SchedulerConfig(ConfigBase):
    router_service_url: str

    database: DatabaseConfig = DatabaseConfig()

    max_data_date: date = date(2017, 5, 10)


scheduler_config = SchedulerConfig()