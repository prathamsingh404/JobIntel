import re
import unicodedata
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from bs4 import BeautifulSoup
from app.utils.logger import logger

class JobCleaner:
    """HTML sanitization, tracking parameter removal, and unicode normalization pipeline."""

    @staticmethod
    def clean_html(html_content: str) -> str:
        """Strips HTML tags and extracts plain text recursively."""
        if not html_content:
            return ""
        try:
            # We use BeautifulSoup with lxml for speed
            soup = BeautifulSoup(html_content, "lxml")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text(separator=" ")
            return text
        except Exception as e:
            logger.warning(f"BeautifulSoup parsing failed: {e}. Falling back to regex stripper.")
            # Fallback regex stripper
            clean_re = re.compile('<.*?>')
            return re.sub(clean_re, ' ', html_content)

    @staticmethod
    def clean_url(url: str) -> str:
        """Removes tracking query parameters (like utm_source, ref) from URLs."""
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            # Filter tracking parameters
            tracking_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid"}
            qsl = parse_qsl(parsed.query)
            filtered_qsl = [(k, v) for k, v in qsl if k.lower() not in tracking_params]
            
            # Reconstruct URL without tracking params
            clean_query = urlencode(filtered_qsl)
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                clean_query,
                parsed.fragment
            ))
            return clean_url
        except Exception as e:
            logger.warning(f"Failed to clean URL {url}: {e}")
            return url

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Standardizes unicode characters (collapsing smart quotes, fractional entities, etc.)."""
        if not text:
            return ""
        # NFKC standardizes characters like \xa0 (non-breaking space) or custom symbols
        normalized = unicodedata.normalize("NFKC", text)
        
        # Replace common unicode quotes and hyphens
        replacements = {
            "\u201c": '"', "\u201d": '"',  # Smart quotes
            "\u2018": "'", "\u2019": "'",  # Smart apostrophes
            "\u2013": "-", "\u2014": "-",  # En/Em dash
            "\u2022": "*",                 # Bullet point
        }
        for orig, rep in replacements.items():
            normalized = normalized.replace(orig, rep)
            
        return normalized

    @staticmethod
    def remove_emojis_and_symbols(text: str) -> str:
        """Strips emojis, symbols, and non-printable characters."""
        if not text:
            return ""
        # Strip emoji unicodes
        emoji_pattern = re.compile(
            "["
            "\U00010000-\U0010ffff"  # Supplemental planes (emojis, etc.)
            "\u2600-\u27BF"          # Miscellaneous symbols, Dingbats
            "\u2000-\u32FF"          # Punctuation/symbols
            "]+",
            flags=re.UNICODE
        )
        cleaned = emoji_pattern.sub("", text)
        return cleaned

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapses duplicate newlines, spaces, and tabs."""
        if not text:
            return ""
        # Collapse multiple spaces or tabs
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse three or more newlines into double newlines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Remove leading/trailing space on each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        return text.strip()

    @staticmethod
    def is_english(text: str) -> bool:
        """A simple, dependency-free stop-words count to check if text is English."""
        if not text:
            return False
        english_stopwords = {"the", "and", "this", "that", "with", "from", "for", "your", "will", "have"}
        words = re.findall(r"\b[a-z]{3,15}\b", text.lower())
        if not words:
            return False
        stopword_count = sum(1 for w in words if w in english_stopwords)
        ratio = stopword_count / len(words) if words else 0
        # If at least 2% of words are standard English stopwords, it's English.
        # This is extremely fast and robust for job descriptions.
        return stopword_count >= 3 or ratio > 0.02

    def clean(self, raw_html: str) -> str:
        """Executes full cleaning pipeline and returns clean plain text."""
        # 1. Strip HTML tags
        text = self.clean_html(raw_html)
        # 2. Normalize Unicode
        text = self.normalize_unicode(text)
        # 3. Strip Emojis
        text = self.remove_emojis_and_symbols(text)
        # 4. Standardize whitespace
        text = self.normalize_whitespace(text)
        return text
