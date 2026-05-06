FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only what the API needs at runtime
COPY src/ ./src/
COPY assets/ ./assets/

# Persistent memory lives here; Cloud Run writes are ephemeral
RUN mkdir -p outputs

# Cloud Run injects PORT (default 8080); fall back to 8080 locally
ENV PORT=8080

CMD uvicorn src.api:app --host 0.0.0.0 --port $PORT
