import time
import logging
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
from agentql import wrap, configure

from config import (
    AGENTQL_API_KEY,
    HOTEL_LIST_QUERY,
    OVERALL_REVIEW_STATS_QUERY,
    INDIVIDUAL_REVIEWS_QUERY,
    DEFAULT_VIEWPORT,
    DEFAULT_USER_AGENT
)
from utils import save_data

# Configure AgentQL
if AGENTQL_API_KEY:
    configure(api_key=AGENTQL_API_KEY)

class AgodaScraper:
    def __init__(self, headless: bool = False, slow_mo: int = 300, logger: logging.Logger = None):
        self.headless = headless
        self.slow_mo = slow_mo
        self.logger = logger or logging.getLogger(__name__)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Initialize Playwright and Browser."""
        self.logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo if not self.headless else 0
        )
        self.context = self.browser.new_context(
            viewport=DEFAULT_VIEWPORT,
            user_agent=DEFAULT_USER_AGENT
        )
        self.page = wrap(self.context.new_page())
        self.logger.info("Browser started.")

    def close(self):
        """Close browser resources."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logger.info("Browser closed.")

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
            self.logger.debug("Right-click activation success.")
        except Exception as e:
            self.logger.warning(f"Right-click activation failed: {e}")

    def _turn_off_overlay(self):
        """Attempt to close overlays/backdrops."""
        try:
            backdrop = self.page.locator("[data-selenium='backdrop']")
            if backdrop.count() > 0 and backdrop.first.is_visible():
                self.logger.info("Backdrop detected, attempting to close...")
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
                self.logger.info("Backdrop disabled via JS.")
        except Exception as e:
            self.logger.debug(f"Overlay handling error: {e}")

    def navigate(self, url: str, max_retries: int = 3):
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Navigating to {url} (Attempt {attempt + 1}/{max_retries})")
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                self.page.wait_for_timeout(2000)
                self._activate_page()
                return True
            except Exception as e:
                self.logger.warning(f"Navigation failed: {e}")
                if attempt < max_retries - 1:
                    self.page.wait_for_timeout(2000)
                else:
                    self.logger.error("All navigation retries failed.")
                    raise
        return False

    def _click_read_all_reviews(self) -> bool:
        """Click 'Read all reviews' button."""
        self.logger.info("Attempting to click 'Read all reviews'...")
        locator = self.page.locator("span[label='Read all reviews']")
        
        try:
            if not locator.is_visible():
                self._turn_off_overlay()
            
            locator.click(force=True, timeout=5000)
            self.logger.info("Clicked 'Read all reviews'.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to click 'Read all reviews': {e}")
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
        self.logger.info(f"Scraping hotel: {url}")
        self.navigate(url)
        
        hotel_name = self.page.title().split(" - ")[0] if " - " in self.page.title() else "Unknown Hotel"
        self.logger.info(f"Hotel Name: {hotel_name}")

        if self._click_read_all_reviews():
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                self.page.wait_for_timeout(1500)

        # Overall Stats
        overall_stats = {}
        try:
            overall_stats = self.page.query_data(OVERALL_REVIEW_STATS_QUERY, timeout=10000)
            self.logger.info(f"Overall Score: {overall_stats.get('overall_score', 'N/A')}")
        except Exception as e:
            self.logger.warning(f"Failed to get overall stats: {e}")

        # Reviews
        all_reviews = []
        page_num = 1
        
        while len(all_reviews) < max_reviews:
            self.logger.info(f"Scraping reviews page {page_num}...")
            try:
                data = self.page.query_data(INDIVIDUAL_REVIEWS_QUERY, timeout=15000)
                reviews = data.get("reviews", [])
                
                if not reviews:
                    self.logger.info("No reviews found on this page.")
                    break
                
                all_reviews.extend(reviews)
                self.logger.info(f"Collected {len(reviews)} reviews. Total: {len(all_reviews)}/{max_reviews}")
                
                if len(all_reviews) >= max_reviews:
                    break
                
                if not self._click_next_page():
                    self.logger.info("No next page found.")
                    break
                
                page_num += 1
            except Exception as e:
                self.logger.error(f"Error scraping reviews: {e}")
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
        self.logger.info(f"Searching hotels at: {search_url}")
        self.navigate(search_url)
        
        # Scroll to load
        for _ in range(3):
            self.page.keyboard.press("PageDown")
            time.sleep(1)

        hotels_list = []
        try:
            data = self.page.query_data(HOTEL_LIST_QUERY, timeout=15000)
            hotels_list = data.get("hotels", [])
            self.logger.info(f"Found {len(hotels_list)} hotels.")
        except Exception as e:
            self.logger.error(f"Failed to get hotel list: {e}")
            return []

        results = []
        target_hotels = hotels_list[:max_hotels]
        
        for i, hotel in enumerate(target_hotels):
            url = hotel.get("hotel_link")
            if not url:
                continue
            
            if url.startswith("/"):
                url = "https://www.agoda.com" + url
            
            self.logger.info(f"Processing hotel {i+1}/{len(target_hotels)}")
            try:
                data = self.scrape_hotel(url, max_reviews=reviews_per_hotel)
                results.append(data)
                save_data(results, "agoda_reviews.json", self.logger)
            except Exception as e:
                self.logger.error(f"Failed to scrape hotel {url}: {e}")
            
            if i < len(target_hotels) - 1:
                time.sleep(3)
        
        return results
