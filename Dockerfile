FROM python:3.12-slim  # Use 3.12 as in runtime.txt; change to 3.14 if needed

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Port - Timeweb sets $PORT automatically
# Default if $PORT not set
ENV PORT=8080

# Run via Gunicorn from requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "2", "admin_panel:app"]
