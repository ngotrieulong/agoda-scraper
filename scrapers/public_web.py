"""
CATEGORY 1: Simple Public Website Scraper

USE CASE EXAMPLES:
- B2B company research (contact info, team size)
- Product catalogs scraping
- Blog post aggregation
- Wikipedia data extraction
"""

import sys
sys.path.append('..')

from utils.content_fetcher import ContentFetcher
from utils.llm_extractor import LLMExtractor
import json

# DEFINE YOUR DATA SCHEMA
# Đây là structure bạn muốn extract
COMPANY_SCHEMA = {
    "name": "company_info",
    "schema": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "Official company name"
            },
            "industry": {
                "type": "string",
                "description": "Primary industry/sector"
            },
            "employee_count": {
                "type": "string",
                "description": "Number of employees (e.g., '50-100', '500+')"
            },
            "headquarters": {
                "type": "string",
                "description": "HQ location (city, country)"
            },
            "description": {
                "type": "string",
                "description": "Brief company description"
            },
            "technologies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Technologies/tools they use"
            },
            "contact_email": {
                "type": "string",
                "description": "General contact email if available"
            }
        },
        "required": ["company_name", "industry", "description"],
        "additionalProperties": False
    }
}

def scrape_companies(urls: list) -> list:
    """
    Main scraping function
    
    WORKFLOW:
    1. Fetch markdown from URLs (via Jina)
    2. Extract structured data (via OpenAI)
    3. Return clean JSON list
    """
    
    # Initialize components
    fetcher = ContentFetcher()
    extractor = LLMExtractor()
    
    print(f"🚀 Starting scrape for {len(urls)} companies...")
    
    # Step 1: Fetch content
    print("\n📡 Fetching content...")
    content_dict = fetcher.fetch_multiple(urls)
    print(f"✅ Fetched {len(content_dict)} pages")
    
    # Step 2: Extract data
    print("\n🤖 Extracting structured data...")
    results = extractor.batch_extract(content_dict, COMPANY_SCHEMA)
    print(f"✅ Extracted {len(results)} records")
    
    return results

def main():
    """
    Example usage
    """
    
    # Target URLs - Replace with your targets
    target_urls = [
        "https://www.anthropic.com/company",
        "https://openai.com/about",
        "https://www.deepmind.com/about"
    ]
    
    # Run scraper
    data = scrape_companies(target_urls)
    
    # Save results
    output_file = "../data/outputs/companies.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(data)} records to {output_file}")
    
    # Preview
    print("\n📊 Sample result:")
    print(json.dumps(data[0], indent=2))

if __name__ == "__main__":
    main()