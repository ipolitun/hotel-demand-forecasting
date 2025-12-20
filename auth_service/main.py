import logging

from fastapi import FastAPI

from auth_service.api.routers import auth, users, hotels
from shared.errors import (
    register_error_handlers,
    setup_openapi_with_errors,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Auth Service API")
    register_error_handlers(app)
    setup_openapi_with_errors(app)

    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(users.router, prefix="/users", tags=["Users"])
    app.include_router(hotels.router, prefix="/hotels", tags=["Hotels"])

    @app.get("/", tags=["system"])
    async def root():
        return {"message": "AUTH_SERVICE is running"}

    return app


app = create_app()
