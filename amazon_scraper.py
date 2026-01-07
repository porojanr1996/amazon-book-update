"""
Amazon BSR (Best Sellers Rank) Scraper
Extracts BSR values from Amazon product pages
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import Optional, Dict
import logging
import sys
from pathlib import Path

# Add project root to path to import bsr_parser
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from app.utils.bsr_parser import parse_bsr
except ImportError:
    # Fallback if bsr_parser not available
    parse_bsr = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AmazonScraper:
    def __init__(self, delay_between_requests: float = 2.0, retry_attempts: int = 3):
        self.delay_between_requests = delay_between_requests
        self.retry_attempts = retry_attempts
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate realistic headers for Amazon requests"""
        # Use a fixed, realistic User-Agent instead of random to avoid detection
        # Amazon may block or return different content for random User-Agents
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def extract_bsr(self, amazon_url: str, use_playwright: bool = False) -> Optional[int]:
        """
        Extract BSR (Best Sellers Rank) from Amazon product page
        
        Args:
            amazon_url: Full Amazon product URL
            use_playwright: If True, use Playwright for extraction (more reliable for UK/blocked pages)
            
        Returns:
            BSR value as integer, or None if not found
        """
        # For UK domains, always use Playwright (Amazon UK blocks simple requests)
        is_uk_domain = '.co.uk' in amazon_url or 'amazon.co.uk' in amazon_url
        if is_uk_domain:
            logger.info(f"UK domain detected, using Playwright for {amazon_url}")
            use_playwright = True
        
        # If Playwright is requested, use it directly
        if use_playwright:
            try:
                from app.services.playwright_scraper import extract_bsr_with_playwright_sync
                bsr = extract_bsr_with_playwright_sync(amazon_url)
                if bsr:
                    return bsr
                # If Playwright fails, try simple method as fallback
                logger.warning(f"Playwright extraction failed, trying simple method as fallback")
            except Exception as e:
                logger.warning(f"Playwright extraction failed, trying simple method: {e}")
        
        # Clean URL - remove /ref and other parameters that might cause issues
        # Also fix common URL issues like missing slashes
        clean_url = amazon_url.split('/ref')[0].split('?')[0].rstrip('/')
        
        # Fix common URL issues: amazon.co.ukgp -> amazon.co.uk/gp
        if '.ukgp' in clean_url:
            clean_url = clean_url.replace('.ukgp', '.uk/gp')
        if '.comgp' in clean_url:
            clean_url = clean_url.replace('.comgp', '.com/gp')
        
        if not clean_url.endswith('/'):
            clean_url += '/'
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Attempting to scrape BSR from {clean_url} (attempt {attempt + 1}/{self.retry_attempts})")
                
                headers = self._get_headers()
                response = self.session.get(clean_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Use strict BSR parser to extract main BSR (prioritizes "in Kindle Store" over category rankings)
                if parse_bsr:
                    html_content = response.content.decode('utf-8', errors='ignore')
                    bsr = parse_bsr(html_content)
                    if bsr:
                        logger.info(f"✅ Extracted BSR using strict parser: #{bsr:,}")
                        return bsr
                    else:
                        logger.warning(f"Strict parser did not find BSR on page: {clean_url}")
                else:
                    # Fallback to old method if parser not available
                    logger.warning("Strict BSR parser not available, using fallback method")
                    soup = BeautifulSoup(response.content, 'lxml')
                    
                    # Try to find main BSR (prioritize "in Kindle Store")
                    page_text = soup.get_text()
                    bsr_patterns = [
                        r'Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',  # Main BSR
                        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',  # Direct main BSR
                    ]
                    for pattern in bsr_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            bsr_str = match.group(1).replace(',', '')
                            bsr_value = int(bsr_str)
                            if 1 <= bsr_value < 10000000:  # Validate range
                                logger.info(f"✅ Extracted BSR using fallback: #{bsr_value:,}")
                                return bsr_value
                
                logger.warning(f"BSR not found on page: {clean_url}")
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.delay_between_requests * (attempt + 1))
                else:
                    logger.error(f"Failed to scrape BSR after {self.retry_attempts} attempts")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None
            
            finally:
                # Be respectful with rate limiting
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.delay_between_requests)
        
        return None
    
    def extract_book_info(self, amazon_url: str) -> Optional[Dict[str, str]]:
        """
        Extract additional book information (title, author, cover image, price, reviews)
        
        Args:
            amazon_url: Full Amazon product URL
            
        Returns:
            Dictionary with book info or None
        """
        try:
            headers = self._get_headers()
            response = self.session.get(amazon_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            info = {}
            
            # Extract title
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                info['title'] = title_elem.get_text().strip()
            
            # Extract author
            author_elem = soup.find('a', {'class': 'a-link-normal', 'href': re.compile(r'/gp/product/.*author')})
            if not author_elem:
                author_elem = soup.find('span', {'class': 'author'})
            if author_elem:
                info['author'] = author_elem.get_text().strip()
            
            # Extract cover image
            img_elem = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'id': 'imgBlkFront'})
            if img_elem and img_elem.get('src'):
                info['cover_image'] = img_elem['src']
            
            # Extract price
            price_elem = soup.find('span', {'class': 'a-price-whole'})
            if price_elem:
                price_fraction = soup.find('span', {'class': 'a-price-fraction'})
                if price_fraction:
                    info['price'] = f"{price_elem.get_text()}.{price_fraction.get_text()}"
            
            # Extract review count
            review_elem = soup.find('span', {'id': 'acrCustomerReviewText'})
            if review_elem:
                info['reviews'] = review_elem.get_text().strip()
            
            return info if info else None
            
        except Exception as e:
            logger.error(f"Error extracting book info: {e}")
            return None
    
    def extract_cover_image(self, amazon_url: str, use_playwright: bool = False) -> Optional[str]:
        """
        Extract cover image URL from Amazon product page
        
        Args:
            amazon_url: Full Amazon product URL
            use_playwright: If True, use Playwright for extraction (more reliable)
            
        Returns:
            Cover image URL as string, or None if not found
        """
        # Validate that amazon_url is actually a URL (not a BSR number or invalid data)
        if not amazon_url or not isinstance(amazon_url, str):
            logger.warning(f"Invalid amazon_url provided: {amazon_url}")
            return None
        
        if not amazon_url.startswith(('http://', 'https://', 'www.')):
            logger.warning(f"Invalid amazon_url format (not a URL): {amazon_url[:50]}")
            return None
    
        if use_playwright:
            try:
                from app.services.playwright_scraper import extract_cover_image_with_playwright_sync
                return extract_cover_image_with_playwright_sync(amazon_url)
            except Exception as e:
                logger.warning(f"Playwright extraction failed, trying simple method: {e}")
        
        # Simple method using requests
        try:
            clean_url = amazon_url.split('/ref')[0].split('?')[0].rstrip('/')
            
            # Fix common URL issues: amazon.co.ukgp -> amazon.co.uk/gp
            if '.ukgp' in clean_url:
                clean_url = clean_url.replace('.ukgp', '.uk/gp')
            if '.comgp' in clean_url:
                clean_url = clean_url.replace('.comgp', '.com/gp')
            
            if not clean_url.endswith('/'):
                clean_url += '/'
            
            headers = self._get_headers()
            response = self.session.get(clean_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try multiple selectors for cover image
            img_elem = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'id': 'imgBlkFront'})
            if img_elem and img_elem.get('src'):
                cover_url = img_elem['src']
                # Clean up image URL for better quality
                cover_url = re.sub(r'_SL\d+_', '_SL800_', cover_url)
                cover_url = re.sub(r'\._AC_[^_]+_', '._AC_SL800_', cover_url)
                if '_SL' not in cover_url:
                    cover_url = cover_url.replace('._AC_', '._AC_SL800_')
                cover_url = re.sub(r'_SX\d+_', '_SX800_', cover_url)
                return cover_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting cover image: {e}")
            return None

