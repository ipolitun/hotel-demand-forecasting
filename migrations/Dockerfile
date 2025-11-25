FROM python:3.11

WORKDIR /app

COPY ./migrations/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY shared ./shared

ENV PYTHONPATH=/app

CMD ["alembic", "upgrade", "head"]
