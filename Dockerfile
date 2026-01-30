FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем сертификат PostgreSQL (если он у тебя есть)
RUN mkdir -p /root/.postgresql
COPY certs/timeweb-ca.crt /root/.postgresql/root.crt 2>/dev/null || echo "Сертификат не найден, пропускаем"
RUN chmod 0600 /root/.postgresql/root.crt 2>/dev/null || true

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Вот эта строка — именно она определяет, как запускать приложение на Timeweb
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:$PORT", "main:app"]
