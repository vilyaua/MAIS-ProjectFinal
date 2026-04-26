# --- Build stage ---
FROM python:3.13-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Runtime stage ---
FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN mkdir -p workspace output logs

ENTRYPOINT ["python", "main.py"]
