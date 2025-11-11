FROM python:3.13-slim

WORKDIR /app
COPY ./auth_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./auth_service /app/auth_service
COPY ./shared /app/shared

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
