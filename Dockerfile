FROM python:3.12-slim

# Установка libpq
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Создаём директорию и копируем сертификат (если файл не найден — сборка не упадёт)
RUN mkdir -p /root/.postgresql
COPY certs/timeweb-ca.crt /root/.postgresql/root.crt || true
RUN chmod 0600 /root/.postgresql/root.crt || true

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:$PORT", "main:app"]
