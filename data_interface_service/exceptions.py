from fastapi import status


class ServiceError(Exception):
    """Базовый класс для всех бизнес-ошибок микросервиса."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Внутренняя ошибка сервиса"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class AuthorizationError(ServiceError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Неверный идентификатор отеля"


class InsufficientHistoryError(ServiceError):
    """Недостаточно данных для прогноза."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Недостаточно данных для формирования прогноза"


class NoForecastError(ServiceError):
    """Прогноз отсутствует."""
    status_code = status.HTTP_404_NOT_FOUND
    message = "Прогноз отсутствует для указанного периода"


class CSVProcessingError(ServiceError):
    """Ошибка при чтении, валидации или нормализации CSV."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Ошибка обработки CSV-файла"


class MappingError(ServiceError):
    """Ошибка при маппинге."""
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Ошибка преобразования"


class DatabaseError(ServiceError):
    """Ошибка при сохранении или взаимодействии с БД."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Ошибка сохранения данных в базу"


class ConflictError(ServiceError):
    """Конфликт данных — например, все записи уже существуют."""
    status_code = status.HTTP_409_CONFLICT
    message = "Все записи уже существуют, новые не добавлены"
