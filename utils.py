import logging
import json
import os
from typing import List, Dict

def setup_logging(log_file: str = "scraper.log"):
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("AgodaScraper")

def save_data(data: List[Dict], filename: str, logger=None):
    """Save data to JSON atomically."""
    temp_file = f"{filename}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, filename)
        if logger:
            logger.info(f"Saved data to {filename}")
    except Exception as e:
        if logger:
            logger.error(f"Failed to save data: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
