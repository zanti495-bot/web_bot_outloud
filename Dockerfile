# Use 3.12 as in runtime.txt; change to 3.14 if needed
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2-binary
RUN apt-get update -y && \
    apt-get install -y libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy root.crt for SSL verify-full
COPY root.crt /root/.postgresql/root.crt

# Copy the rest of the code
COPY . .

# Port - fixed to 8080
ENV PORT=8080

# Run via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "admin_panel:app"]
