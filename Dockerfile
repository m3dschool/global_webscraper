FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Playwright
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Create non-root user first
RUN useradd --create-home --shell /bin/bash webscraper

# Install Playwright browsers as root in global location
RUN playwright install chromium --with-deps

# Copy browsers to user-accessible location and set ownership
RUN mkdir -p /home/webscraper/.cache/ms-playwright && \
    cp -r /root/.cache/ms-playwright/* /home/webscraper/.cache/ms-playwright/ && \
    chown -R webscraper:webscraper /home/webscraper/.cache

# Set ownership of app directory
RUN chown -R webscraper:webscraper /app

# Switch to non-root user
USER webscraper

# Expose ports
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]