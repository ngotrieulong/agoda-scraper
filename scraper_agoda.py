import os
import time
import json
import logging
import argparse
from typing import List, Dict, Optional
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from agentql import wrap, configure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
AGENTQL_API_KEY = os.getenv("AGENTQL_API_KEY")
if AGENTQL_API_KEY:
    configure(api_key=AGENTQL_API_KEY)
else:
    logger.warning("AGENTQL_API_KEY not found in .env")

# --- QUERIES ---
HOTEL_LIST_QUERY = """
{
    hotels[] {
        hotel_name
        hotel_link
        rating (Optional)
        review_count (Optional)
    }
}
"""

OVERALL_REVIEW_STATS_QUERY = """
{
    overall_score
    overall_rating_text
    total_reviews
    recent_ratings[] {
        rating_value
    }
    review_categories[] {
        category_name
        category_score
    }
}
"""

INDIVIDUAL_REVIEWS_QUERY = """
{
    reviews[] {
        reviewer_score
        reviewer_score_text
        reviewer_name
        reviewer_country
        traveler_type (Optional)
        room_type (Optional)
        stay_duration (Optional)
        review_title
        review_text
        review_date
    }
}
"""

class AgodaScraper:
    def __init__(self, headless: bool = False, slow_mo: int = 300):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Initialize Playwright and Browser."""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo if not self.headless else 0
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = wrap(self.context.new_page())
        logger.info("Browser started.")

    def close(self):
        """Close browser resources."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed.")

    def _activate_page(self):
        """Right-click to activate Agoda DOM to avoid pointer event interception."""
        try:
            self.page.wait_for_timeout(1000)
            self.page.keyboard.press("PageDown")
            self.page.wait_for_timeout(300)
            
            vp = self.page.viewport_size
            cx, cy = vp["width"] // 2, vp["height"] // 2
            
            self.page.mouse.move(cx, cy)
            self.page.mouse.click(cx, cy, button="right")
            self.page.wait_for_timeout(500)
            logger.debug("Right-click activation success.")
        except Exception as e:
            logger.warning(f"Right-click activation failed: {e}")

    def _turn_off_overlay(self):
        """Attempt to close overlays/backdrops."""
        try:
            backdrop = self.page.locator("[data-selenium='backdrop']")
            if backdrop.count() > 0 and backdrop.first.is_visible():
                logger.info("Backdrop detected, attempting to close...")
                try:
                    backdrop.first.click()
                    self.page.wait_for_timeout(200)
                    return
                except:
                    pass
                
                try:
                    self.page.keyboard.press("Escape")
                    self.page.wait_for_timeout(200)
                    return
                except:
                    pass

                # JS Force remove
                self.page.evaluate("""
                    () => {
                        const b = document.querySelector("[data-selenium='backdrop']");
                        if (b) {
                            b.style.pointerEvents = 'none';
                            b.style.opacity = '0';
                        }
                    }
                """)
                self.page.wait_for_timeout(200)
                logger.info("Backdrop disabled via JS.")
        except Exception as e:
            logger.debug(f"Overlay handling error: {e}")

    def navigate(self, url: str, max_retries: int = 3):
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to {url} (Attempt {attempt + 1}/{max_retries})")
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                self.page.wait_for_timeout(2000)
                self._activate_page()
                return True
            except Exception as e:
                logger.warning(f"Navigation failed: {e}")
                if attempt < max_retries - 1:
                    self.page.wait_for_timeout(2000)
                else:
                    logger.error("All navigation retries failed.")
                    raise
        return False

    def _click_read_all_reviews(self) -> bool:
        """Click 'Read all reviews' button."""
        logger.info("Attempting to click 'Read all reviews'...")
        locator = self.page.locator("span[label='Read all reviews']")
        
        try:
            if not locator.is_visible():
                self._turn_off_overlay()
            
            locator.click(force=True, timeout=5000)
            logger.info("Clicked 'Read all reviews'.")
            return True
        except Exception as e:
            logger.error(f"Failed to click 'Read all reviews': {e}")
            return False

    def _click_next_page(self) -> bool:
        """Click next pagination button."""
        sel = "button[aria-label='Next reviews page'], button[data-element-name='review-paginator-next'], button[aria-label*='Next']"
        loc = self.page.locator(sel)
        
        count = loc.count()
        if count == 0:
            return False

        for i in range(count):
            cand = loc.nth(i)
            if cand.is_visible():
                try:
                    cand.click(force=True, timeout=5000)
                    try:
                        self.page.wait_for_load_state("networkidle", timeout=5000)
                    except:
                        self.page.wait_for_timeout(500)
                    return True
                except:
                    continue
        return False

    def scrape_hotel(self, url: str, max_reviews: int = 50) -> Dict:
        """Scrape a single hotel."""
        logger.info(f"Scraping hotel: {url}")
        self.navigate(url)
        
        hotel_name = self.page.title().split(" - ")[0] if " - " in self.page.title() else "Unknown Hotel"
        logger.info(f"Hotel Name: {hotel_name}")

        if self._click_read_all_reviews():
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                self.page.wait_for_timeout(1500)

        # Overall Stats
        overall_stats = {}
        try:
            overall_stats = self.page.query_data(OVERALL_REVIEW_STATS_QUERY, timeout=10000)
            logger.info(f"Overall Score: {overall_stats.get('overall_score', 'N/A')}")
        except Exception as e:
            logger.warning(f"Failed to get overall stats: {e}")

        # Reviews
        all_reviews = []
        page_num = 1
        
        while len(all_reviews) < max_reviews:
            logger.info(f"Scraping reviews page {page_num}...")
            try:
                data = self.page.query_data(INDIVIDUAL_REVIEWS_QUERY, timeout=15000)
                reviews = data.get("reviews", [])
                
                if not reviews:
                    logger.info("No reviews found on this page.")
                    break
                
                all_reviews.extend(reviews)
                logger.info(f"Collected {len(reviews)} reviews. Total: {len(all_reviews)}/{max_reviews}")
                
                if len(all_reviews) >= max_reviews:
                    break
                
                if not self._click_next_page():
                    logger.info("No next page found.")
                    break
                
                page_num += 1
            except Exception as e:
                logger.error(f"Error scraping reviews: {e}")
                break

        return {
            "hotel_name": hotel_name,
            "hotel_url": url,
            "overall_statistics": overall_stats,
            "total_reviews_scraped": len(all_reviews),
            "reviews": all_reviews[:max_reviews]
        }

    def scrape_multiple(self, search_url: str, max_hotels: int = 3, reviews_per_hotel: int = 20) -> List[Dict]:
        """Scrape multiple hotels from search results."""
        logger.info(f"Searching hotels at: {search_url}")
        self.navigate(search_url)
        
        # Scroll to load
        for _ in range(3):
            self.page.keyboard.press("PageDown")
            time.sleep(1)

        hotels_list = []
        try:
            data = self.page.query_data(HOTEL_LIST_QUERY, timeout=15000)
            hotels_list = data.get("hotels", [])
            logger.info(f"Found {len(hotels_list)} hotels.")
        except Exception as e:
            logger.error(f"Failed to get hotel list: {e}")
            return []

        results = []
        target_hotels = hotels_list[:max_hotels]
        
        for i, hotel in enumerate(target_hotels):
            url = hotel.get("hotel_link")
            if not url:
                continue
            
            if url.startswith("/"):
                url = "https://www.agoda.com" + url
            
            logger.info(f"Processing hotel {i+1}/{len(target_hotels)}")
            try:
                data = self.scrape_hotel(url, max_reviews=reviews_per_hotel)
                results.append(data)
                self.save_data(results, "agoda_reviews.json")
            except Exception as e:
                logger.error(f"Failed to scrape hotel {url}: {e}")
            
            if i < len(target_hotels) - 1:
                time.sleep(3)
        
        return results

    @staticmethod
    def save_data(data: List[Dict], filename: str):
        """Save data to JSON atomically."""
        temp_file = f"{filename}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, filename)
            logger.info(f"Saved data to {filename}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

def main():
    parser = argparse.ArgumentParser(description="Agoda Hotel Reviews Scraper")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--max-hotels", type=int, default=3, help="Max hotels to scrape")
    parser.add_argument("--reviews", type=int, default=20, help="Reviews per hotel")
    parser.add_argument("--url", type=str, 
                       default="https://www.agoda.com/city/da-nang-vn.html?ds=tCjgS9%2FXlnLw8%2F0G",
                       help="Search URL")
    parser.add_argument("--mode", choices=["multiple", "single"], default="multiple", help="Scrape mode")
    parser.add_argument("--single-url", type=str, help="URL for single hotel mode")
    
    args = parser.parse_args()

    scraper = AgodaScraper(headless=args.headless)
    try:
        scraper.start()
        
        if args.mode == "single":
            if not args.single_url:
                logger.error("Single mode requires --single-url")
                return
            data = scraper.scrape_hotel(args.single_url, max_reviews=args.reviews)
            AgodaScraper.save_data([data], "agoda_reviews.json")
        else:
            scraper.scrape_multiple(args.url, max_hotels=args.max_hotels, reviews_per_hotel=args.reviews)
            
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
