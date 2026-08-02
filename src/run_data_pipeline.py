import os
import logging
from dotenv import load_dotenv
from src.scraper.web_scraper import WebScraper

load_dotenv()
logging.basicConfig(level=logging.INFO)

def main():
    target_url = os.getenv("TARGET_URL")
    max_pages = int(os.getenv("SCRAPE_MAX_PAGES", "5"))
    min_words = int(os.getenv("MIN_WORDS", "10"))
    output_file = "data/raw/scraped_data.json"

    logging.info("1. Starting Scraping...")
    scraper = WebScraper(base_url=target_url, min_words=min_words, max_pages=max_pages)
    scraper.scrape_page(target_url)
    scraper.save_data(output_file)

if __name__ == "__main__":
    main()