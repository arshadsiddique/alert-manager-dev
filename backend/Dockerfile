FROM python:3.11-slim

WORKDIR /app

ENV TZ=Etc/GMT
# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    tzdata \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy startup script and make it executable
COPY startup.sh .
RUN chmod +x startup.sh

# Copy alembic configuration
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy application code
COPY app/ ./app/

# Create empty __init__.py files
RUN touch app/__init__.py \
    && touch app/models/__init__.py \
    && touch app/schemas/__init__.py \
    && touch app/services/__init__.py \
    && touch app/api/__init__.py \
    && touch app/api/routes/__init__.py \
    && touch app/core/__init__.py \
    && touch app/utils/__init__.py

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["./startup.sh"]
