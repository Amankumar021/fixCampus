FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY ml/ /app/ml/
COPY infrastructure/ /app/infrastructure/

RUN mkdir -p /app/data/uploads \
    && useradd --create-home --shell /usr/sbin/nologin campusfix \
    && chown -R campusfix:campusfix /app
USER campusfix

EXPOSE 8000

CMD ["sh", "-c", "alembic -c /app/backend/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
