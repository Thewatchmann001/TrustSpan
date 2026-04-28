# TrustSpan Backend — Python 3.12
FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2, python-magic, and optional native libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Install torch CPU-only FIRST to avoid pulling the massive CUDA wheel (~1.5GB)
# sentence-transformers will reuse this install
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# App and deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use env DATABASE_URL at runtime
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Run migrations then start API (override CMD for migrations-only if needed)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
