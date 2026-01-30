FROM python:3.12-slim

WORKDIR /app

# Устанавливаем libpq5 для psycopg2-binary
RUN apt-get update -y && \
    apt-get install -y libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "admin_panel:app"]
