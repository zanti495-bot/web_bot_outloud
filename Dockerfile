FROM python:3.12-slim

WORKDIR /app

ARG CACHE_BUSTER=2026-02-01-v2

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY ca.crt /app/ca.crt

RUN echo "CACHE_BUSTER=${CACHE_BUSTER}" > /app/.cachebuster.txt && \
    cat /app/.cachebuster.txt

RUN chmod 644 /app/ca.crt && ls -lh /app/ca.crt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "1", \
     "--timeout", "180", \
     "app:app"]