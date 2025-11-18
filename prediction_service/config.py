from pathlib import Path

from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig


class PredictionServiceConfig(ConfigBase):
    model_dir: Path = Path("prediction_service/models")

    database: DatabaseConfig = DatabaseConfig()


prediction_config = PredictionServiceConfig()
