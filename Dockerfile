FROM python:3.12-slim

WORKDIR /app

# Устанавливаем wget + ca-certificates (на всякий случай обновляем системные сертификаты)
RUN apt-get update && apt-get install -y wget ca-certificates \
    && update-ca-certificates

# Скачиваем сертификат Timeweb + сразу проверяем, что он скачался
RUN wget -O /app/ca.crt https://st.timeweb.com/cloud-static/ca.crt \
    && ls -l /app/ca.crt \
    && head -n 5 /app/ca.crt || echo "Сертификат не скачан или пустой" \
    && chmod 644 /app/ca.crt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "main:app"]