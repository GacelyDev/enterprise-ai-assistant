import os
import logging
from dotenv import load_dotenv
from src.scraper.web_scraper import WebScraper
from src.scraper.ingest import ingest_data_to_vectordb

load_dotenv()
logging.basicConfig(level=logging.INFO)

def main():
    target_url = os.getenv("TARGET_URL")
    max_pages = int(os.getenv("SCRAPE_MAX_PAGES", "5"))
    min_words = int(os.getenv("MIN_WORDS", "10"))
    output_file = "data/raw/scraped_data.json"
    chunk_size = int(os.getenv("CHUNK_SIZE", "1024"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "128"))
    host = os.getenv("VECTOR_DB_HOST", "vector_db")
    port = int(os.getenv("VECTOR_DB_PORT", "8000"))

    logging.info("1. Starting Scraping...")
    scraper = WebScraper(base_url=target_url, min_words=min_words, max_pages=max_pages)
    scraper.scrape_page(target_url)
    scraper.save_data(output_file)

    logging.info("2. Starting Ingestion to VectorDB...")
    ingest_data_to_vectordb(
        json_path=output_file,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        host=host,
        port=port
    )

if __name__ == "__main__":
    main()