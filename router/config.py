from pydantic import Field
from pydantic_settings import SettingsConfigDict

from shared.base_config import ConfigBase


class JWTConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str
    hash_algorithm: str = "HS256"


class RouterConfig(ConfigBase):
    jwt_config: JWTConfig = Field(default_factory=JWTConfig)

    prediction_service_url: str = "http://prediction_service:8001"
    auth_service_url: str = "http://auth-service:8002"
    data_interface_service_url: str = "http://data-interface-service:8003"
    frontend_url: str = "http://frontend:8080"


router_config = RouterConfig()
