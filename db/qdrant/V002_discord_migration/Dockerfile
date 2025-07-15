FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for PostgreSQL and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash migration-user

# Copy requirements first for better Docker layer caching
COPY v002_requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r v002_requirements.txt

# Copy migration scripts
COPY V002_migrate_discord_pgvector.py .
COPY V002_verify_migration.py .

# Change ownership to non-root user
RUN chown -R migration-user:migration-user /app

# Switch to non-root user
USER migration-user

# Set environment variables for better Python behavior in containers
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command (can be overridden)
ENTRYPOINT ["python", "V002_migrate_discord_pgvector.py"]
CMD ["--help"]