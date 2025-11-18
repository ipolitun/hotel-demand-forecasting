from shared.base_config import ConfigBase


class RouterConfig(ConfigBase):
    prediction_service_url: str = "http://prediction_service:8001"
    auth_service_url: str = "http://auth-service:8002"
    data_interface_service_url: str = "http://data-interface-service:8003"

    secret_key: str
    algorithm: str = "HS256"


router_config = RouterConfig()
