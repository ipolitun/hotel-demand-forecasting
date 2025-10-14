import logging
from datetime import datetime, date
from shared.db import get_sync_session
from scheduler_service.config import ROUTER_SERVICE_URL, MAX_DATA_DATE
import httpx

logger = logging.getLogger(__name__)

def trigger_forecast():
    logger.info("[%s] Запуск задачи trigger_forecast()", datetime.now())
    session = get_sync_session()

    try:
        # TODO: заменить на динамическое получение из БД
        hotel_ids = [1]
        logger.info("[%s] Найдены отели: %s", datetime.now(), hotel_ids)
    except Exception as e:
        logger.error("[%s] Ошибка при получении hotel_id: %s", datetime.now(), e)
        return

    today = datetime.utcnow().date()
    target_date = min(today, date.fromisoformat(MAX_DATA_DATE))

    for hotel_id in hotel_ids:
        for has_deposit in [False]:
            payload = {
                "hotel_id": hotel_id,
                "target_date": target_date.isoformat(),
                "has_deposit": has_deposit,
            }

            try:
                response = httpx.post(
                    f"{ROUTER_SERVICE_URL}/prediction/run-prediction",
                    json=payload,
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(
                        "[%s] Прогноз получен: hotel_id=%s, has_deposit=%s",
                        datetime.now(), hotel_id, has_deposit
                    )
                else:
                    logger.error(
                        "[%s] Ошибка от ROUTER %s: %s",
                        datetime.now(), response.status_code, response.text
                    )
            except Exception as e:
                logger.error("[%s] Ошибка при отправке запроса: %s", datetime.now(), e)
