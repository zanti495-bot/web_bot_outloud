FROM python:3.12-slim

# Установка зависимостей PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Создаём директорию
RUN mkdir -p /root/.postgresql

# Копируем сертификат — важно точное имя файла из git!
COPY certs/timeweb-ca.crt /root/.postgresql/root.crt

# Права доступа
RUN chmod 0600 /root/.postgresql/root.crt

# Отладка: показываем, что лежит в директории и первые строки файла
RUN echo "=== Содержимое /root/.postgresql ===" && \
    ls -la /root/.postgresql && \
    if [ -f /root/.postgresql/root.crt ]; then echo "Файл найден! Первые 5 строк:" && head -n 5 /root/.postgresql/root.crt; else echo "Файл НЕ найден!"; fi

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
