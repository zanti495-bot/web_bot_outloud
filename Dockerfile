FROM python:3.12-slim  # Используем 3.12, как в runtime.txt; если нужно 3.14, измените

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Порт — Timeweb задаёт $PORT автоматически
ENV PORT=8080  # Дефолт, если $PORT не задан

# Запуск через Gunicorn (из requirements.txt)
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "2", "admin_panel:app"]
