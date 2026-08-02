import re

class TextCleaner:
    """
    Utility class to clean and normalize text extracted from web scraping
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        if not raw_text:
            return ""
        # 1. Convert to lowercase
        text = raw_text.lower()

        # 2. Remove multiple line breaks and carriage returns
        text = re.sub(r'[\r\n]+', ' ', text)

        # 3. Remove multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)

        return text.strip()

    @staticmethod
    def is_valid_paragraph(text: str, min_words: int = 10) -> bool:
        """
        Filter out text fragments that are too short (e.g., buttons like 'Accept', 'Read more')
        """
        words = text.split()
        return len(words) >= min_words