FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY docs/ ./docs/
COPY contracts/ ./contracts/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/static && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]