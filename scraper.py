import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional, List

# Setup logging
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def scrape_data(urls: Optional[List[str]] = None) -> Optional[str]:
    """
    Scrapes text content from a list of URLs and concatenates them.

    Args:
        urls (Optional[List[str]]): List of target URLs to scrape.

    Returns:
        Optional[str]: The extracted text content concatenated, or None if scraping all fails.
    """
    if urls is None:
        urls = [
            "https://news.ycombinator.com/",
            "https://github.com/trending",
            "https://dev.to/top/week"
        ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    concatenated_texts = []

    for url in urls:
        try:
            logging.info(f"Mencoba melakukan scraping pada URL: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # Check for HTTP errors

            soup = BeautifulSoup(response.content, 'html.parser')

            # Ekstrak semua teks, buang tag HTML
            text_content = soup.get_text(separator=' ', strip=True)

            concatenated_texts.append(f"--- SUMBER: {url} ---\n{text_content}\n")
            logging.info(f"Scraping berhasil dilakukan untuk URL: {url}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Gagal melakukan request ke URL {url}. Error: {e}")
        except Exception as e:
            logging.error(f"Terjadi kesalahan tak terduga saat scraping {url}. Error: {e}")

    if concatenated_texts:
        return "\n".join(concatenated_texts)
    else:
        logging.error("Semua target URL gagal di-scrape.")
        return None

if __name__ == "__main__":
    # Test (Placeholder)
    sample_text = scrape_data()
    # print omitted as per requirement. We will verify via logs.
