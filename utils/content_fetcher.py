import requests
from typing import Optional

class ContentFetcher:
    """
    Fetch LLM-optimized content from websites
    Using Jina AI Reader (FREE tier)
    """
    
    def __init__(self):
        self.jina_base = "https://r.jina.ai/"
    
    def fetch_with_jina(self, url: str) -> Optional[str]:
        """
        Convert any website to clean markdown
        
        HOW IT WORKS:
        1. Prepend https://r.jina.ai/ to any URL
        2. Jina returns markdown instead of HTML
        3. No API key needed for basic usage!
        
        Example:
            url = "https://example.com"
            content = fetcher.fetch_with_jina(url)
        """
        try:
            jina_url = f"{self.jina_base}{url}"
            response = requests.get(jina_url, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Error: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Fetch error: {e}")
            return None
    
    def fetch_multiple(self, urls: list) -> dict:
        """
        Fetch multiple URLs efficiently
        Returns: {url: content}
        """
        results = {}
        for url in urls:
            print(f"Fetching: {url}")
            content = self.fetch_with_jina(url)
            if content:
                results[url] = content
        return results