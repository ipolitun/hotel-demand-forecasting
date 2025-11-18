FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y bash

COPY ./scripts/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./shared /app/shared
COPY ./scripts /app/scripts

ENV PYTHONPATH=/app