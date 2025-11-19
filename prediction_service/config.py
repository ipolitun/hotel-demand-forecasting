from pathlib import Path
from pydantic import Field

from shared.base_config import ConfigBase
from shared.db_config import DatabaseConfig


class PredictionServiceConfig(ConfigBase):
    model_dir: Path = Path("prediction_service/models")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)


prediction_config = PredictionServiceConfig()
