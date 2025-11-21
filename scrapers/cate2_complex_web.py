"""
CATEGORY 2: Complex Website Scraper with Authentication

USE CASES:
- Job boards (requiring login)
- E-commerce competitor pricing
- Social media data extraction
- Premium content scraping
"""

import sys
sys.path.append('..')

from utils.browser_handler import BrowserHandler
import os
import time
import json

class JobBoardScraper:
    """
    Example: Scraping job board requiring authentication
    """
    
    def __init__(self, login_url: str, target_url: str):
        self.login_url = login_url
        self.target_url = target_url
        self.state_file = "session_state.json"
        self.browser = BrowserHandler(headless=False)  # Show browser for debugging
    
    def login(self, email: str, password: str):
        """
        Perform login workflow
        
        AGENTQL QUERIES - Explaining the magic:
        
        Instead of writing:
          element = driver.find_element_by_id("email_input_id_123")
        
        With AgentQL you write:
          "email input field in login form"
        
        ADVANTAGES:
        ✅ Works even if website redesigns
        ✅ Works across different sites
        ✅ No need to inspect HTML
        ❌ Slightly slower (AI processing)
        """
        
        print("🔐 Starting login process...")
        
        # Start browser
        page = self.browser.start_session()
        
        # Navigate to login page
        page.goto(self.login_url)
        time.sleep(2)  # Wait for page load
        
        # STEP 1: Find and fill email
        print("📧 Entering email...")
        self.browser.find_and_type(
            "email input field in login form",
            email,
            wait_after=1000
        )
        
        # STEP 2: Click continue/next button
        print("➡️ Clicking continue...")
        self.browser.find_and_click(
            "continue button or next button in login form",
            wait_after=2000
        )
        
        # STEP 3: Handle "I'm not a robot" if present
        print("🤖 Checking for CAPTCHA...")
        captcha_handled = self.browser.find_and_click(
            "I'm not a robot checkbox",
            wait_after=2000
        )
        
        if captcha_handled:
            print("✅ CAPTCHA clicked (ironically by AI)")
        
        # STEP 4: Enter password (if shown)
        print("🔑 Entering password...")
        self.browser.find_and_type(
            "password input field",
            password,
            wait_after=1000
        )
        
        # STEP 5: Click final login button
        print("🚀 Logging in...")
        self.browser.find_and_click(
            "login button or sign in button",
            wait_after=3000
        )
        
        # STEP 6: Save session state
        self.browser.save_session(self.state_file)
        print("✅ Login successful! Session saved.")
    
    def scrape_jobs(self) -> list:
        """
        Scrape job listings with pagination
        
        PAGINATION STRATEGY:
        ┌─────────────────┐
        │ Page 1          │
        │ └─ Get jobs     │
        │ └─ Click Next   │
        └────────┬────────┘
                 │
                 ↓
        ┌─────────────────┐
        │ Page 2          │
        │ └─ Get jobs     │
        │ └─ Click Next   │
        └────────┬────────┘
                 │
                 ↓ (repeat until no next button)
        ┌─────────────────┐
        │ All jobs        │
        │ collected!      │
        └─────────────────┘
        """
        
        # Load saved session (no need to login again!)
        page = self.browser.load_session(self.state_file)
        
        if not page:
            print("❌ No saved session. Please login first.")
            return []
        
        all_jobs = []
        page_num = 1
        has_next_page = True
        
        # Navigate to job listings
        page.goto(self.target_url)
        time.sleep(2)
        
        while has_next_page:
            print(f"\n📄 Scraping page {page_num}...")
            
            # Define data structure to extract
            job_query = {
                "job_posts": [
                    {
                        "company_name": "Company or organization name",
                        "job_title": "Job title or position name",
                        "location": "Job location",
                        "salary": "Salary range if shown",
                        "contract_type": "Full-time, part-time, or contract",
                        "remote_type": "Remote, hybrid, or on-site"
                    }
                ]
            }
            
            # Extract jobs from current page
            data = self.browser.extract_data(job_query)
            
            if data and 'job_posts' in data:
                jobs_on_page = data['job_posts']
                all_jobs.extend(jobs_on_page)
                print(f"✅ Found {len(jobs_on_page)} jobs on page {page_num}")
            
            # Try to click "Next" button
            current_url = page.url
            next_clicked = self.browser.find_and_click(
                "next page button or pagination next button",
                wait_after=2000
            )
            
            # Check if URL changed (means we moved to next page)
            if next_clicked and page.url != current_url:
                page_num += 1
                has_next_page = True
            else:
                print("🏁 Reached last page")
                has_next_page = False
        
        return all_jobs
    
    def save_to_airtable(self, jobs: list):
        """
        Save scraped jobs to Airtable
        
        AIRTABLE = Simple database cho non-technical users
        Think of it as: Excel + Database + API
        
        SETUP:
        1. Create account at airtable.com
        2. Create a base (= database)
        3. Create table with columns matching your data
        4. Get API key from account settings
        """
        
        from pyairtable import Api
        
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        table = api.table(
            os.getenv('AIRTABLE_BASE_ID'),
            os.getenv('AIRTABLE_TABLE_NAME')
        )
        
        print(f"\n💾 Saving {len(jobs)} jobs to Airtable...")
        
        for job in jobs:
            try:
                table.create(job)
            except Exception as e:
                print(f"Error saving job: {e}")
        
        print("✅ All jobs saved to Airtable!")
    
    def close(self):
        """Clean up"""
        self.browser.close()

def main():
    """
    Example usage
    """
    
    # Configuration
    LOGIN_URL = "https://www.idealist.org/en/login"
    TARGET_URL = "https://www.idealist.org/en/jobs"
    
    EMAIL = os.getenv('TARGET_SITE_EMAIL')
    PASSWORD = os.getenv('TARGET_SITE_PASSWORD')
    
    # Initialize scraper
    scraper = JobBoardScraper(LOGIN_URL, TARGET_URL)
    
    # Check if we have saved session
    if not os.path.exists("session_state.json"):
        print("🔐 No saved session. Performing login...")
        scraper.login(EMAIL, PASSWORD)
    else:
        print("✅ Using saved session")
    
    # Scrape jobs
    jobs = scraper.scrape_jobs()
    
    # Save results
    with open('../data/outputs/jobs.json', 'w') as f:
        json.dump(jobs, f, indent=2)
    
    print(f"\n📊 Total jobs scraped: {len(jobs)}")
    
    # Optional: Save to Airtable
    # scraper.save_to_airtable(jobs)
    
    # Cleanup
    scraper.close()

if __name__ == "__main__":
    main()