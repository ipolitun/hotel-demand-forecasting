FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ python3-dev libffi-dev

COPY ./prediction_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./prediction_service /app/prediction_service
COPY ./shared /app/shared

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "prediction_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
