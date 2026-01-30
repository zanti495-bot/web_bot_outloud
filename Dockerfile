FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget

RUN wget -O ca.crt https://st.timeweb.com/cloud-static/ca.crt

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "main:app"]