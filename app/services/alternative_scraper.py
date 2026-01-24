"""
Alternative scraping methods when Amazon blocks direct access
"""
import logging
import re
from typing import Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_bsr_via_alternative_method(amazon_url: str) -> Optional[int]:
    """
    Alternative method to extract BSR when direct scraping is blocked
    
    Methods tried:
    1. Amazon mobile page (sometimes less protected)
    2. Amazon API endpoints (if available)
    3. Third-party services (if configured)
    
    Args:
        amazon_url: Amazon product URL
        
    Returns:
        BSR value or None
    """
    # Method 1: Try Amazon mobile page
    mobile_url = amazon_url.replace('www.amazon.com', 'www.amazon.com/gp/aw/d')
    mobile_url = mobile_url.replace('/dp/', '/dp/')
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(mobile_url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            # Try to extract BSR from mobile page
            bsr = _extract_bsr_from_html(html)
            if bsr:
                logger.info(f"✅ BSR extracted from mobile page: #{bsr:,}")
                return bsr
    except Exception as e:
        logger.debug(f"Mobile page method failed: {e}")
    
    # Method 2: Try to extract ASIN and use alternative endpoints
    asin = _extract_asin(amazon_url)
    if asin:
        # Try Amazon's product API endpoint (sometimes works)
        try:
            api_url = f"https://www.amazon.com/dp/{asin}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            # This might not work, but worth trying
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                html = response.text
                bsr = _extract_bsr_from_html(html)
                if bsr:
                    return bsr
        except Exception as e:
            logger.debug(f"API endpoint method failed: {e}")
    
    return None


def _extract_asin(url: str) -> Optional[str]:
    """Extract ASIN from Amazon URL"""
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _extract_bsr_from_html(html: str) -> Optional[int]:
    """Extract BSR from HTML using multiple patterns"""
    if not html:
        return None
    
    # Try strict parser first
    try:
        from app.utils.bsr_parser import parse_bsr
        bsr = parse_bsr(html)
        if bsr:
            return bsr
    except:
        pass
    
    # Fallback: aggressive regex search
    patterns = [
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        r'Best\s+Sellers\s+Rank[:\s]*#?(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
        r'SalesRank[:\s]*#?(\d{1,3}(?:,\d{3})*)',
        r'rank[:\s]*#?(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            try:
                bsr_value = int(match.replace(',', ''))
                if 1 <= bsr_value < 10000000:
                    return bsr_value
            except:
                continue
    
    return None

