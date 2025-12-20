import logging
import uuid
from typing import Type

from fastapi import Request, FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)


# === Базовый класс ошибок микросервисов ===
class ServiceError(Exception):
    """
    Базовый класс для контролируемых ошибок микросервисов.
    Обеспечивает единый формат ответов и централизованную обработку ошибок во всех сервисах системы.
    """
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    type: str = "ServiceError"
    message: str = "Internal service error"
    code: str | None = None

    def __init__(self, message: str | None = None, code: str | None = None):
        if message:
            self.message = message
        if code:
            self.code = code
        super().__init__(self.message)


# === Базовые и инфраструктурные ошибки ===

class AuthorizationError(ServiceError):
    status_code = status.HTTP_401_UNAUTHORIZED
    type = "AuthorizationError"
    message = "Неверный идентификатор отеля или API-ключ"


class NotFoundError(ServiceError):
    status_code = status.HTTP_404_NOT_FOUND
    type = "NotFoundError"
    message = "Данные не найдены"


class ValidationError(ServiceError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    type = "ValidationError"
    message = "Ошибка валидации входных данных"


class ConflictError(ServiceError):
    status_code = status.HTTP_409_CONFLICT
    type = "ConflictError"
    message = "Конфликт данных"


class DatabaseError(ServiceError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    type = "DatabaseError"
    message = "Ошибка взаимодействия с базой данных"


class ExternalServiceError(ServiceError):
    status_code = status.HTTP_502_BAD_GATEWAY
    type = "ExternalServiceError"
    message = "Ошибка при обращении к внешнему сервису"


# === Ошибки, связанные с моделями машинного обучения ===

class ModelNotFoundError(ServiceError):
    status_code = status.HTTP_404_NOT_FOUND
    type = "ModelNotFoundError"
    message = "Файл модели или конфигурация не найдены"


class ModelConfigError(ServiceError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    type = "ModelConfigError"
    message = "Ошибка валидации конфигурации модели"


# === Доменные ошибки (для data_interface_service и моделей) ===

class CSVProcessingError(ServiceError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    type = "CSVProcessingError"
    message = "Ошибка обработки CSV-файла"


class MappingError(ServiceError):
    status_code = status.HTTP_400_BAD_REQUEST
    type = "MappingError"
    message = "Ошибка преобразования данных"


class InsufficientHistoryError(ServiceError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    type = "InsufficientHistoryError"
    message = "Недостаточно данных для формирования прогноза"


class NoForecastError(ServiceError):
    status_code = status.HTTP_404_NOT_FOUND
    type = "NoForecastError"
    message = "Прогноз отсутствует для указанного периода"


# === Универсальный формат ответа ===

def format_error_response(exc: ServiceError, trace_id: str | None = None) -> dict:
    """Формирует стандартную структуру JSON-ответа об ошибке."""
    if not exc.code:
        exc.code = "_".join(
            [part.upper() for part in exc.type.replace("-", "_").split("_")]
        )

    return {
        "error": {
            "type": exc.type,
            "message": exc.message,
            "code": exc.code or exc.type.upper(),
            "trace_id": trace_id,
        }
    }


# === Регистрация глобальных обработчиков ===

def register_error_handlers(app: FastAPI):
    """
    Регистрирует глобальные обработчики ошибок и middleware для trace_id.
    Должен вызываться в каждом микросервисе один раз при инициализации FastAPI.
    """

    # --- Middleware для trace_id ---
    @app.middleware("http")
    async def add_trace_id_middleware(request: Request, call_next):
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        try:
            response = await call_next(request)
        except Exception:
            raise
        else:
            response.headers["X-Trace-ID"] = trace_id
            return response

    # --- Обработка предсказуемых (контролируемых) ошибок ---
    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(f"[{exc.type}] {exc.message} (trace_id={trace_id})")
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc, trace_id),
        )

    # --- Обработка непредусмотренных ошибок ---
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", None)
        logger.exception(f"Unhandled exception (trace_id={trace_id})", exc_info=exc)
        generic = ServiceError("Unexpected internal error", code="INTERNAL_ERROR")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=format_error_response(generic, trace_id),
        )


# === Регистрация ошибок для Swagger ===

def register_errors(*error_classes: Type[ServiceError]):
    """
    Декоратор для регистрации возможных ошибок эндпоинта.
    """
    def decorator(func):
        setattr(func, "__errors__", list(error_classes))
        return func
    return decorator


def extend_openapi_with_errors(app: FastAPI):
    """
    Добавляет зарегистрированные ошибки (@register_errors) в документацию OpenAPI/Swagger.
    """
    # Генерация схемы, если её ещё нет
    if not getattr(app, "openapi_schema", None):
        app.openapi()

    schema = app.openapi_schema
    if not schema or "paths" not in schema:
        return schema

    for route in app.routes:
        # Обрабатываем только реальные HTTP-эндпоинты
        if not isinstance(route, APIRoute):
            continue

        endpoint = getattr(route, "endpoint", None)
        if not endpoint or not hasattr(endpoint, "__errors__"):
            continue

        # Добавляем зарегистрированные ошибки в схему OpenAPI
        for error_cls in getattr(endpoint, "__errors__", []):
            for method, method_data in schema["paths"].get(route.path, {}).items():
                responses = method_data.setdefault("responses", {})

                responses[str(error_cls.status_code)] = {
                    "description": getattr(error_cls, "message", "Service error"),
                    "content": {
                        "application/json": {
                            "example": format_error_response(error_cls())
                        }
                    },
                }

    return app.openapi_schema


def setup_openapi_with_errors(app: FastAPI):
    """Подключает автоматическое добавление ошибок в OpenAPI."""
    original_openapi = app.openapi

    def custom_openapi():
        # если схема уже сгенерирована — возвращаем кэш
        if app.openapi_schema:
            return app.openapi_schema

        # генерируем базовую схему (через исходную функцию FastAPI)
        base_schema = original_openapi()

        # дополняем схему зарегистрированными ошибками
        app.openapi_schema = extend_openapi_with_errors(app)

        return app.openapi_schema

    app.openapi = custom_openapi