from fastapi import FastAPI
from data_interface_service.routers.booking_router import router as upload_router
from data_interface_service.routers.forecast_router import router as prediction_router

app = FastAPI(title="Data Interface Service API")

app.include_router(upload_router, prefix="/booking")
app.include_router(prediction_router, prefix="/forecast")

@app.get("/")
def root():
    return {"message": "Data Interface Service is running"}
