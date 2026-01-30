FROM python:3.12-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Скачивание сертификата Timeweb
RUN wget -O /etc/ssl/certs/ca.crt https://st.timeweb.com/cloud-static/ca.crt

# Установка рабочей директории
WORKDIR /app

# Копирование файлов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск через gunicorn + uvicorn
CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]