FROM python:3.12-slim

# Установка зависимостей для PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Запуск
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
