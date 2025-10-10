FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ python3-dev libffi-dev

COPY ./data_interface_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./data_interface_service /app/data_interface_service
COPY ./shared /app/shared
COPY ./database /app/database

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "data_interface_service.main:app", "--host", "0.0.0.0", "--port", "8003"]
