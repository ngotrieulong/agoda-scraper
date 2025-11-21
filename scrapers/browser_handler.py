from playwright.sync_api import sync_playwright, Page, Browser
from agentql.ext.playwright.sync_api import wrap
import time
import os
import json

class BrowserHandler:
    """
    Handle browser automation with AI-powered element detection
    """
    
    def __init__(self, headless: bool = False):
        """
        Args:
            headless: Run browser without UI (faster, for production)
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def start_session(self, save_state: bool = True):
        """
        Start new browser session
        
        WHAT HAPPENS:
        1. Launch Chromium browser
        2. Create new context (like incognito window)
        3. Wrap with AgentQL for AI element detection
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )
        
        # Create context (isolated session)
        self.context = self.browser.new_context()
        
        # Wrap with AgentQL
        self.page = wrap(self.context.new_page())
        
        print("✅ Browser session started")
        return self.page
    
    def load_session(self, state_file: str):
        """
        Load saved login session
        
        WHY USEFUL:
        - Không cần login lại mỗi lần
        - Save time và avoid rate limits
        - Cookies + auth tokens preserved
        """
        if not os.path.exists(state_file):
            print(f"⚠️ State file not found: {state_file}")
            return self.start_session()
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )
        
        # Load saved state
        self.context = self.browser.new_context(
            storage_state=state_file
        )
        self.page = wrap(self.context.new_page())
        
        print(f"✅ Loaded session from {state_file}")
        return self.page
    
    def save_session(self, state_file: str):
        """Save current session state"""
        if self.context:
            self.context.storage_state(path=state_file)
            print(f"💾 Session saved to {state_file}")
    
    def find_and_click(self, query: str, wait_after: int = 1000):
        """
        Find element using natural language and click
        
        HOW AGENTQL WORKS:
        ┌──────────────────┐
        │ "login button"   │ ← Your natural language
        └────────┬─────────┘
                 │
                 ↓ AI Vision
        ┌──────────────────┐
        │ Scan all UI      │ ← AgentQL analyzes page
        │ elements         │
        └────────┬─────────┘
                 │
                 ↓ Match
        ┌──────────────────┐
        │ Return correct   │ ← Even if button text is
        │ button element   │    "Sign In" or "Log In"!
        └──────────────────┘
        
        Args:
            query: Natural language description
            wait_after: Milliseconds to wait after click
        """
        try:
            element = self.page.query_elements(query)
            if element:
                element.click()
                time.sleep(wait_after / 1000)
                print(f"✅ Clicked: {query}")
                return True
            else:
                print(f"❌ Not found: {query}")
                return False
        except Exception as e:
            print(f"Error clicking {query}: {e}")
            return False
    
    def find_and_type(self, query: str, text: str, wait_after: int = 500):
        """
        Find input field and type text
        """
        try:
            element = self.page.query_elements(query)
            if element:
                element.fill(text)
                time.sleep(wait_after / 1000)
                print(f"✅ Typed into: {query}")
                return True
            else:
                print(f"❌ Not found: {query}")
                return False
        except Exception as e:
            print(f"Error typing into {query}: {e}")
            return False
    
    def extract_data(self, query: dict) -> dict:
        """
        Extract structured data using AgentQL
        
        Example query:
        {
            "job_posts": [
                {
                    "company_name": "Company name",
                    "job_title": "Job title",
                    "salary": "Salary range",
                    "location": "Location"
                }
            ]
        }
        """
        try:
            data = self.page.query_data(query)
            return data
        except Exception as e:
            print(f"Error extracting data: {e}")
            return {}
    
    def close(self):
        """Clean up resources"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🔚 Browser session closed")