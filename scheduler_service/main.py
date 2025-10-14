import logging
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager

from scheduler_service.jobs import trigger_forecast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[%s] Lifespan: запуск планировщика", datetime.now())
    trigger_forecast()
    yield
    logger.info("[%s] Lifespan: завершение работы", datetime.now())


app = FastAPI(title="Scheduler Service API", lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Scheduler Service is running"}
