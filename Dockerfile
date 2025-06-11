FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data/indexes

# Set environment variables
ENV PYTHONPATH=/app
ENV SECURITY_ASSISTANT_DATA=/app/data

# Make scripts executable
RUN chmod +x /app/app/ingest.py /app/app/query.py

# Expose API port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
