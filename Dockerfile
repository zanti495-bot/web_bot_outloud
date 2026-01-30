FROM python:3.12-slim

# Установка libpq для PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Создаём директорию для сертификата PostgreSQL (стандартный путь libpq/psycopg2)
RUN mkdir -p /root/.postgresql

# Копируем сертификат из репозитория в контейнер
COPY certs/timeweb-ca.crt /root/.postgresql/root.crt

# Права только для чтения
RUN chmod 0600 /root/.postgresql/root.crt

WORKDIR /app
COPY . /app

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
