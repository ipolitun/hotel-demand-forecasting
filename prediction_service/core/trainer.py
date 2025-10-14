import logging
import torch
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
from shutil import copytree
from sqlalchemy.orm import Session

from prediction_service.core.model_loader import load_model_config
from prediction_service.core.gru_model import GRUForecaster
from prediction_service.preprocessing.preprocessor import preprocess_data
from prediction_service.preprocessing.scaling import normalize_data
from prediction_service.preprocessing.sequencing import create_sequences
from shared.data_loader import load_bookings, load_weather, load_holidays

logger = logging.getLogger(__name__)


def setup_hotel_model_from_base(hotel_id: int):
    """
    Копирует базовую модель и конфиг как шаблон для нового отеля.
    """
    base_path = Path("prediction_service/base_model")
    hotel_path = Path(f"prediction_service/models/hotel_{hotel_id}")

    if hotel_path.exists():
        logger.info(f"Модель для hotel_{hotel_id} уже существует — пропуск копирования.")
        return

    copytree(base_path, hotel_path)
    logger.info(f"Базовая модель успешно скопирована для hotel_{hotel_id}.")


def train_model_for_hotel(
    hotel_id: int,
    db_session: Session,
    target_col: str = "bookings",
    window_size: int = 30,
    epochs: int = 10,
    batch_size: int = 32,
):
    """
    Обучает модель прогнозирования для указанного отеля.
    """
    logger.info(f"Начало обучения модели для hotel_id={hotel_id}")

    # --- Загрузка конфигурации ---
    config = load_model_config(hotel_id)

    model = GRUForecaster(
        num_numeric_features=len(config["numeric_features"]),
        embedding_sizes={k: tuple(v) for k, v in config["embedding_sizes"].items()},
        hidden_size=config["hidden_size"],
        gru_layers=config["gru_layers"],
        dropout=config["dropout"],
        forecast_horizon=config["forecast_horizon"],
        output_dims=config["output_dims"],
    )

    # --- Загрузка весов (если есть) ---
    model_path = Path(f"prediction_service/models/hotel_{hotel_id}/model.pt")
    if model_path.exists():
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        logger.info(f"Загружена существующая модель из {model_path}")
    else:
        logger.warning(f"Файл весов {model_path} не найден — обучение начнётся с нуля.")

    # --- Загрузка данных ---
    logger.info("Загрузка данных бронирований, погоды и праздников...")
    df_b = load_bookings(hotel_id, db_session)
    df_w = load_weather(hotel_id, db_session)
    df_h = load_holidays(db_session)

    df = df_b.merge(df_w, left_on="arrival_date", right_on="date", how="left")
    df["is_holiday"] = df["arrival_date"].isin(df_h["date"]).astype(int)

    # --- Предобработка ---
    logger.info("Предобработка и нормализация данных...")
    df_processed = preprocess_data(df)
    df_scaled = normalize_data(df_processed, config["numeric_features"])

    # --- Создание обучающих последовательностей ---
    X_np, Y_np = create_sequences(df_scaled, config["numeric_features"], target_col, window_size)
    X_tensor = torch.tensor(X_np, dtype=torch.float32)
    Y_tensor = torch.tensor(Y_np, dtype=torch.float32)

    dataset = TensorDataset(X_tensor, Y_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # --- Обучение модели ---
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.get("learning_rate", 0.001),
        weight_decay=config.get("weight_decay", 0.0001),
    )
    criterion = torch.nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_X, batch_Y in loader:
            optimizer.zero_grad()
            output = model(batch_X)
            loss = criterion(output, batch_Y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        logger.info(f"Epoch {epoch + 1}/{epochs} — Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), model_path)
    logger.info(f"Модель сохранена: {model_path}")

    logger.info(f"Обучение модели для hotel_id={hotel_id} завершено успешно.")
