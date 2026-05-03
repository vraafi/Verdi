import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional

# Setup logging
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def scrape_data(url: str) -> Optional[str]:
    """
    Scrapes text content from a given URL.

    Args:
        url (str): The target URL to scrape.

    Returns:
        Optional[str]: The extracted text content, or None if scraping fails.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        logging.info(f"Mencoba melakukan scraping pada URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors

        soup = BeautifulSoup(response.content, 'html.parser')

        # Ekstrak semua teks, buang tag HTML
        text_content = soup.get_text(separator=' ', strip=True)

        logging.info("Scraping berhasil dilakukan.")
        return text_content

    except requests.exceptions.RequestException as e:
        logging.error(f"Gagal melakukan request ke URL {url}. Error: {e}")
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat scraping. Error: {e}")
        return None

if __name__ == "__main__":
    # Test (Placeholder URL)
    sample_text = scrape_data("https://example.com")
    # print omitted as per requirement, but we can verify in log later.
