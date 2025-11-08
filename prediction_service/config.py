import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Директория для хранения моделей
MODEL_DIR = Path(os.getenv("MODEL_DIR", "prediction_service/models"))