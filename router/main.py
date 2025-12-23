import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router.api.routers import auth, data_interface, prediction
from router.config import router_config
from shared.errors import register_error_handlers, setup_openapi_with_errors

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=10)
    logger.info("HTTP client initialized")
    yield
    await app.state.http_client.aclose()
    logger.info("HTTP client closed")


app = FastAPI(title="Router Service API", lifespan=lifespan)

register_error_handlers(app)
setup_openapi_with_errors(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[router_config.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(data_interface.router, prefix="/data", tags=["Data Interface"])
app.include_router(prediction.router, prefix="/prediction", tags=["Prediction"])


@app.get("/")
def root():
    return {"message": "Router Service is running"}
