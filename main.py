import argparse
import logging
import os
from scraper import AgodaScraper
from utils import setup_logging, save_data

def main():
    logger = setup_logging()
    
    parser = argparse.ArgumentParser(description="Agoda Hotel Reviews Scraper")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--max-hotels", type=int, default=3, help="Max hotels to scrape")
    parser.add_argument("--reviews", type=int, default=20, help="Reviews per hotel")
    parser.add_argument("--url", type=str, 
                       default="https://www.agoda.com/city/da-nang-vn.html?ds=tCjgS9%2FXlnLw8%2F0G",
                       help="Search URL")
    parser.add_argument("--mode", choices=["multiple", "single"], default="multiple", help="Scrape mode")
    parser.add_argument("--single-url", type=str, help="URL for single hotel mode")
    parser.add_argument("--output", type=str, default="data/agoda_reviews.json", help="Output .json file path")
    
    args = parser.parse_args()
    output_path = args.output

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    scraper = AgodaScraper(headless=args.headless, logger=logger)
    try:
        scraper.start()
        
        if args.mode == "single":
            if not args.single_url:
                logger.error("Single mode requires --single-url")
                return
            data = scraper.scrape_hotel(args.single_url, max_reviews=args.reviews)
            save_data([data], output_path, logger)
        else:
            reviews = scraper.scrape_multiple(args.url, max_hotels=args.max_hotels, reviews_per_hotel=args.reviews)
            save_data(reviews, output_path, logger)
            
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
