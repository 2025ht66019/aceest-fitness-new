# Multi-stage build (builder for dependencies caching optional)
FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable buffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirement files first for better caching
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source
COPY . .

# Expose flask default port
EXPOSE 5000

# Default command to run the Flask app
CMD ["python", "app/app.py"]
