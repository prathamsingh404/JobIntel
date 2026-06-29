FROM python:3.12-slim

# Set environment variable settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /workspace

# Install system dependencies (needed for lxml, pyarrow, sqlite, and postgres builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code files
COPY app/ app/
COPY config.yaml .
COPY run_pipeline.py .

# Create storage, logs and exports volume mounts
RUN mkdir -p logs exports && chmod -R 777 logs exports

EXPOSE 8000

# Default command starts the Uvicorn web dashboard server
CMD ["python", "run_pipeline.py", "server", "--host", "0.0.0.0", "--port", "8000"]
