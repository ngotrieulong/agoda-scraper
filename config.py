import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
AGENTQL_API_KEY = os.getenv("AGENTQL_API_KEY")

# Default Configuration
DEFAULT_TIMEOUT = 30000
DEFAULT_WAIT_TIMEOUT = 2000
DEFAULT_VIEWPORT = {'width': 1920, 'height': 1080}
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

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
