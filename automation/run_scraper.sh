#!/bin/bash

# Define project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Load environment variables if needed (Docker handles .env file usually, but good for script context)
# source .env

# Pull the latest image (optional, if you want auto-updates)
# docker pull longnt70/agoda-scraper:latest

# Run the scraper using Docker Compose
# This ensures volumes and networks are handled correctly
echo "[$(date)] Starting Agoda Scraper..."
docker-compose run --rm scraper

# Check exit status
if [ $? -eq 0 ]; then
    echo "[$(date)] Scraper finished successfully."
else
    echo "[$(date)] Scraper failed."
fi
