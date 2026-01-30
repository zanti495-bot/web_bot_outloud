FROM python:3.12-slim

WORKDIR /app

# Устанавливаем ca-certificates на всякий случай
RUN apt-get update && apt-get install -y ca-certificates \
    && update-ca-certificates

# Копируем скачанный тобой сертификат
COPY ca.crt /app/ca.crt
RUN chmod 644 /app/ca.crt \
    && ls -l /app/ca.crt \               # Покажет размер в билд-логах
    && head -n 5 /app/ca.crt || echo "Сертификат пустой или не скопирован!"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "main:app"]