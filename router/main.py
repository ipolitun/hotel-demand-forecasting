from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import logging

from router.routers import auth_router, data_interface_router, prediction_router
from shared.errors import register_error_handlers, setup_openapi_with_errors

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_error_handlers(app)
    setup_openapi_with_errors(app)

    app.state.http_client = httpx.AsyncClient(timeout=10)
    logger.info("HTTP client initialized")

    yield

    await app.state.http_client.aclose()
    logger.info("HTTP client closed")

app = FastAPI(title="Router Service API", lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(data_interface_router.router, prefix="/data", tags=["Data Interface"])
app.include_router(prediction_router.router, prefix="/prediction", tags=["Prediction"])

@app.get("/")
def root():
    return {"message": "Router Service is running"}
