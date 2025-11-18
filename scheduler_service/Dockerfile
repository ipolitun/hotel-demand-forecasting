FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ python3-dev libffi-dev

COPY ./scheduler_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./scheduler_service /app/scheduler_service
COPY ./shared /app/shared

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открываем порт для FastAPI
EXPOSE 8004

# Запуск FastAPI через Uvicorn
CMD ["uvicorn", "scheduler_service.main:app", "--host", "0.0.0.0", "--port", "8004"]
