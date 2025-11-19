import torch
import json
import logging
from typing import Tuple, Dict
from torch.nn import Module

from prediction_service.config import prediction_config
from prediction_service.core.gru_model import GRUForecaster
from shared.errors import (
    ServiceError,
    ExternalServiceError,
    ModelNotFoundError,
    ModelConfigError,
)

logger = logging.getLogger(__name__)


def load_model_config(hotel_id: int) -> dict:
    """
    Загружает конфигурационный файл модели для конкретного отеля.

    Returns:
        dict: словарь с параметрами модели.
    """
    config_path = prediction_config.model_dir / f"hotel_{hotel_id}/model_config.json"
    if not config_path.exists():
        raise ModelNotFoundError(f"Конфигурация модели не найдена: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ModelConfigError(f"Ошибка парсинга JSON: {e}")

    required_keys = [
        "numeric_features", "embedding_sizes", "hidden_size",
        "gru_layers", "dropout", "forecast_horizon", "output_dims"
    ]

    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        raise ModelConfigError(f"Отсутствуют обязательные ключи: {', '.join(missing_keys)}")

    logger.info(f"Загружен конфиг модели для hotel_id={hotel_id}")
    return config


def load_model_and_config(hotel_id: int) -> Tuple[Module, dict]:
    """
    Загружает модель и конфигурацию по hotel_id.

    Returns:
        Tuple[torch.nn.Module, dict]: кортеж (модель, конфиг).
    """
    config = load_model_config(hotel_id)

    # Исключаем таргет-признаки
    config["numeric_features"] = [
        col for col in config["numeric_features"]
        if not (col.startswith("book_d") or col.startswith("cancel_d"))
    ]
    config["num_numeric_features"] = len(config["numeric_features"])

    # Приведение embedding_sizes
    try:
        embedding_sizes: Dict[str, Tuple[int, int]] = {
            k: (int(v[0]), int(v[1])) for k, v in config["embedding_sizes"].items()
        }
    except Exception as e:
        raise ModelConfigError(f"Ошибка в формате embedding_sizes: {e}")

    model_path = prediction_config.model_dir / f"hotel_{hotel_id}/model.pt"
    if not model_path.exists():
        raise ModelNotFoundError(f"Файл модели не найден: {model_path}")

    try:
        # Инициализация модели
        model = GRUForecaster(
            num_numeric_features=config["num_numeric_features"],
            embedding_sizes=embedding_sizes,
            hidden_size=int(config["hidden_size"]),
            gru_layers=int(config["gru_layers"]),
            dropout=float(config["dropout"]),
            forecast_horizon=int(config["forecast_horizon"]),
            output_dims=int(config["output_dims"]),
        )
        # Загрузка весов
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
    except RuntimeError as e:
        raise ExternalServiceError(f"Ошибка загрузки весов модели: {e}")
    except Exception as e:
        logger.exception("Непредвиденная ошибка при загрузке модели")
        raise ServiceError(f"Ошибка при инициализации модели: {e}")

    logger.info(f"Модель успешно загружена для hotel_id={hotel_id}")
    return model, config
