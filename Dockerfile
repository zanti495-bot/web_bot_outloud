FROM python:3.14-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Установка порта (Timeweb использует $PORT)
ENV PORT=8080  # Дефолт, если $PORT не задан

# Запуск через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "2", "admin_panel:app"]
