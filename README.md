# Agoda Hotel Scraper

A modular and Dockerized Python scraper for Agoda hotel reviews using Playwright and AgentQL.

## Features
- Scrapes hotel details and reviews.
- Supports single hotel or search result scraping.
- Dockerized for easy deployment.
- Configurable via environment variables and command-line arguments.

## Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local execution)
- AgentQL API Key (Get one at [AgentQL](https://agentql.com/))

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repo_url>
    cd <repo_name>
    ```

2.  **Environment Variables:**
    Create a `.env` file:
    ```bash
    AGENTQL_API_KEY=your_api_key_here
    ```

## Usage

### Using Docker (Recommended)

1.  **Build the image:**
    ```bash
    docker build -t longnt70/agoda-scraper:latest .
    ```

2.  **Run the scraper:**
    ```bash
    docker run --rm \
      -v $(pwd)/data:/app/data \
      --env-file .env \
      longnt70/agoda-scraper:latest \
      --max-hotels 3 --reviews 20 --headless
    ```

    **Command Explanation:**
    *   `--rm`: Automatically remove the container when it exits (keeps your system clean).
    *   `-v $(pwd)/data:/app/data`: Mounts your local `data` folder to `/app/data` inside the container, so scraped files are saved to your machine.
    *   `--env-file .env`: Loads environment variables (API keys, credentials) from your local `.env` file.
    *   `longnt70/agoda-scraper:latest`: The Docker image to run.
    *   `--max-hotels 3 --reviews 20`: Arguments passed to the scraper (scrape 3 hotels, 20 reviews each).

### Running on a New Machine

If you have pulled the image on a fresh machine, follow these steps:

1.  **Create a project directory:**
    ```bash
    mkdir my-scraper
    cd my-scraper
    ```

2.  **Create a `.env` file:**
    Add your API key to a new file named `.env`:
    ```bash
    echo "AGENTQL_API_KEY=your_actual_api_key_here" > .env
    # Add Agoda account credentials (username and password)
    echo "AGODA_USERNAME=your_username" >> .env
    echo "AGODA_PASSWORD=your_password" >> .env
    ```

3.  **Run the scraper:**
    ```bash
    docker run --rm \
      -v $(pwd)/data:/app/data \
      --env-file .env \
      longnt70/agoda-scraper:latest \
      --headless
    ```

### Local Execution

1.  **Install dependencies:**
    ```bash
    pip install -r requirement.txt
    playwright install chromium
    ```

2.  **Run the script:**
    ```bash
    python main.py --max-hotels 3 --reviews 20
    ```

## Automation (Cron Job)

To run the scraper automatically at 2:00 AM every day:

1.  **Edit your crontab:**
    ```bash
    crontab -e
    ```

2.  **Add the following line:**
    ```bash
    0 2 * * * /path/to/your/project/automation/run_scraper.sh >> /path/to/your/project/logs/cron.log 2>&1
    ```
    *Note: Replace `/path/to/your/project` with the actual absolute path.*

## Deployment to Docker Hub

1.  **Login to Docker Hub:**
    ```bash
    docker login
    ```

2.  **Push the image:**
    ```bash
    docker push longnt70/agoda-scraper:latest
    ```
