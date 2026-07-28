# Use Python 3.13.14 slim image
FROM python:3.13.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Production command
# For development, docker-compose overrides this with --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]