FROM python:3.12-slim

# Установка зависимостей для PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Сертификат для SSL
RUN mkdir -p /root/.postgresql
COPY certs/timeweb-ca.crt /root/.postgresql/root.crt
RUN chmod 0600 /root/.postgresql/root.crt

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Запуск app.py и bot.py параллельно
CMD ["sh", "-c", "python app.py & python bot.py"]
