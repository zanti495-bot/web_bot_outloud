# Базовый образ - используем 3.12 как в runtime.txt, при необходимости смените на 3.14
FROM python:3.12-slim

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Порт - Timeweb задаёт $PORT автоматически
# Дефолтное значение, если переменная не пришла
ENV PORT=8080

# Запуск через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "admin_panel:app"]
