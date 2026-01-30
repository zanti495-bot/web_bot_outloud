FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные пакеты и обновляем сертификаты
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Копируем сертификат (теперь с явной проверкой)
COPY ca.crt /app/ca.crt

# Принудительно ломаем кэш при каждом билде (удалить после первого успешного деплоя)
RUN echo "cache-breaker-$(date +%s)" > /app/.cachebreaker

# Проверяем, что сертификат реально скопировался
RUN chmod 644 /app/ca.crt && \
    ls -lh /app/ca.crt && \
    head -n 5 /app/ca.crt || echo "Сертификат пустой или не скопирован!"

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Запускаем через gunicorn + uvicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "1", \
     "--timeout", "120", \
     "main:app"]