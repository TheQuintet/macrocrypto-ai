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
COPY alembic/ ./alembic
COPY alembic.ini ./alembic.ini


# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Production command
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# For local debugging and wouldn't be used in production
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5680", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]