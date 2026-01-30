FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.postgresql
COPY certs/timeweb-ca.crt /root/.postgresql/root.crt || echo "Cert not found, skipping"
RUN chmod 0600 /root/.postgresql/root.crt 2>/dev/null || true

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# CMD указываем только если в Timeweb нет поля Run command
# Лучше задавать в интерфейсе, но на всякий случай:
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "main:app"]
