# Dockerfile for Django Backend
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Django/Daphne typically uses 8000)
EXPOSE 8000

# Default command to run migrations and start the ASGI server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]
