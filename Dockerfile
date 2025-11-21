FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Install Playwright browsers and dependencies
RUN pip install playwright && playwright install --with-deps chromium

# Copy project files
COPY . .

# Create output directory for results
RUN mkdir -p /app/data

# Entry point
ENTRYPOINT ["python", "main.py"]

