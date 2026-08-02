import os
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.scraper.text_cleaner import TextCleaner
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebScraper:
    def __init__(self, base_url: str, min_words: int = 10, max_pages: int = 10):
        self.base_url = base_url
        self.min_words = min_words
        self.max_pages = max_pages
        self.visited_urls = set()
        self.extracted_data = []

        # Start Playwright and launch the Chromium browser
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu"
            ]
        )
        
        # Create a browser context with a custom User-Agent to avoid WAF blocking
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='es-CO'
        )

    def is_valid_url(self, url: str) -> bool:
        """Verify that the URL belongs to the same base domain and is not a file"""
        parsed_url = urlparse(url)
        parsed_base = urlparse(self.base_url)

        # Ignore PDFs, images, etc.
        invalid_extensions = ('.pdf', '.jpg', '.png', '.zip')
        if url.endswith(invalid_extensions):
            return False

        return parsed_url.netloc == parsed_base.netloc

    def scrape_page(self, url: str):
        """Extract the content from a single page using Playwright and search for new links"""
        if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
            return

        logging.info(f"Scraping with Playwright: {url}")
        self.visited_urls.add(url)

        page = None
        try:
            page = self.context.new_page()
            # Navigate and wait for the initial DOM to load
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Brief wait to allow scripts/JavaScript to execute if the page is dynamic
            page.wait_for_timeout(1500)

            html_content = page.content()
            page.close()

            # Validate the received content
            logging.info(f"Total HTML length received: {len(html_content)} characters")

            soup = BeautifulSoup(html_content, 'html.parser')

            # EXTRACTION STRATEGY
            # 1. Try to find the main container of the article/page
            main_content = soup.find('main') or soup.find('article') or soup.find(id='content')

            # 2. If no semantic container is found, fall back to searching the body
            if not main_content:
                main_content = soup.find('body')
                if main_content:
                    for tag in main_content.find_all(['header', 'footer', 'nav']):
                        tag.decompose()

            page_content = []

            # Only if we find a content area, we extract the text
            if main_content:
                # We extract only paragraphs and lists. We avoid <h1> or <h2> if they are very repetitive.
                content_tags = main_content.find_all(['p', 'li'])
                for tag in content_tags:
                    clean_text = TextCleaner.clean_text(tag.get_text())
                    if TextCleaner.is_valid_paragraph(clean_text, min_words=self.min_words):
                        page_content.append(clean_text)

            full_page_text = " ".join(page_content)

            if full_page_text:
                self.extracted_data.append({
                    "url": url,
                    "content": full_page_text
                })

            # Find more links to continue browsing (Basic crawling)
            for link in soup.find_all('a', href=True):
                next_url = urljoin(url, link['href'])
                # Clean up URL fragments (#)
                next_url = next_url.split('#')[0]

                if self.is_valid_url(next_url) and next_url not in self.visited_urls:
                    self.scrape_page(next_url)

        except Exception as e:
            logging.error(f"Error accessing {url} with Playwright: {e}")
            if page and not page.is_closed():
                page.close()

    def close(self):
        """Safely close browser and Playwright resources"""
        if hasattr(self, 'browser') and self.browser:
            self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            self.playwright.stop()

    def save_data(self, output_path: str):
        """Save the extracted data in a JSON file and close browser resources"""
        self.close()
        # Extract the directory name
        dir_name = os.path.dirname(output_path)

        # Only attempt to create folders if the path has a specified directory
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        # Save the file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, ensure_ascii=False, indent=4)

        logging.info(f"Data saved successfully in {output_path}. Total pages: {len(self.extracted_data)}")