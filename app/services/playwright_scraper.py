"""
Playwright-based scraper wrapper for AmazonScraper
Provides async interface for browser-based scraping
"""
import logging
import asyncio
from typing import Optional
from bs4 import BeautifulSoup
import re

from app.services.browser_pool import fetch_page

# Import strict BSR parser
try:
    from app.utils.bsr_parser import parse_bsr as strict_parse_bsr
    STRICT_BSR_PARSER_AVAILABLE = True
except ImportError:
    strict_parse_bsr = None
    STRICT_BSR_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


async def extract_bsr_with_playwright(amazon_url: str) -> Optional[int]:
    """
    Extract BSR using Playwright browser pool
    
    Args:
        amazon_url: Amazon product URL
        
    Returns:
        BSR value as integer, or None if not found
    """
    # Clean URL
    clean_url = amazon_url.split('/ref')[0].split('?')[0].rstrip('/')
    if not clean_url.endswith('/'):
        clean_url += '/'
    
    try:
        logger.debug(f"Fetching page with Playwright for BSR: {clean_url}")
        html = await fetch_page(clean_url, timeout=30000, retries=2)
        
        if not html:
            logger.warning("Failed to fetch page with Playwright")
            return None
        
        # Use strict BSR parser if available - try even if page might be blocked
        if STRICT_BSR_PARSER_AVAILABLE:
            bsr = strict_parse_bsr(html)
            if bsr:
                logger.info(f"✅ BSR extracted with Playwright + strict parser: #{bsr:,}")
                return bsr
            # Even if parser didn't find BSR, check if page has CAPTCHA but might still have BSR
            html_lower = html.lower()
            if 'captcha' in html_lower:
                logger.warning("CAPTCHA detected but attempting to extract BSR anyway...")
                # Try more aggressive parsing
                import re
                # Look for BSR in raw HTML even with CAPTCHA
                bsr_patterns = [
                    r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
                    r'Best\s+Sellers\s+Rank[:\s]*#?(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
                    r'SalesRank[:\s]*#?(\d{1,3}(?:,\d{3})*)',
                ]
                for pattern in bsr_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        try:
                            bsr_value = int(match.replace(',', ''))
                            if 1 <= bsr_value < 10000000:
                                logger.info(f"✅ BSR extracted from blocked page: #{bsr_value:,}")
                                return bsr_value
                        except:
                            continue
            logger.warning("BSR not found even with Playwright + strict parser")
            return None
        
        # Fallback to old method if strict parser not available
        soup = BeautifulSoup(html, 'lxml')
        
        # Try all BSR extraction methods
        # Method 1: SalesRank div
        product_details = soup.find('div', {'id': 'SalesRank'})
        if product_details:
            text = product_details.get_text()
            patterns = [
                r'#(\d+(?:,\d+)*)\s+in\s+.*?\(See\s+Top',
                r'Best Sellers Rank:\s*#(\d+(?:,\d+)*)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    bsr_str = match.group(1).replace(',', '')
                    bsr_value = int(bsr_str)
                    if bsr_value < 10000000:
                        logger.info(f"✓ BSR extracted with Playwright: {bsr_value}")
                        return bsr_value
        
        # Method 2: Search in all text
        page_text = soup.get_text()
        bsr_patterns = [
            r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
            r'Best\s+Sellers\s+Rank.*?#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
            r'#(\d{1,3}(?:,\d{3})*)\s+in\s+.*?Store',
            r'#(\d{1,3}(?:,\d{3})*)\s+in\s+.*?\(See\s+Top',
        ]
        for pattern in bsr_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if match:
                bsr_str = match.group(1).replace(',', '')
                bsr_value = int(bsr_str)
                if bsr_value < 10000000:
                    logger.info(f"✓ BSR extracted with Playwright: {bsr_value}")
                    return bsr_value
        
        logger.warning("BSR not found even with Playwright")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting BSR with Playwright: {e}", exc_info=True)
        return None


async def extract_cover_image_with_playwright(amazon_url: str) -> Optional[str]:
    """
    Extract cover image URL using Playwright browser pool
    
    Args:
        amazon_url: Amazon product URL
        
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
    
    # Clean URL
    clean_url = amazon_url.split('/ref')[0].split('?')[0].rstrip('/')
    if not clean_url.endswith('/'):
        clean_url += '/'
    
    try:
        logger.debug(f"Fetching page with Playwright for cover image: {clean_url}")
        html = await fetch_page(clean_url, timeout=30000, retries=2)
        
        if not html:
            logger.warning("Failed to fetch page with Playwright")
            return None
        
        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Try multiple selectors for cover image
        cover_selectors = [
            {'id': 'landingImage'},
            {'id': 'imgBlkFront'},
            {'id': 'main-image'},
            {'class': 'a-dynamic-image'},
        ]
        
        for selector in cover_selectors:
            img = soup.find('img', selector)
            if img and img.get('src'):
                cover_url = img['src']
                # Clean up image URL for better quality
                cover_url = re.sub(r'_SL\d+_', '_SL800_', cover_url)
                cover_url = re.sub(r'\._AC_[^_]+_', '._AC_SL800_', cover_url)
                if '_SL' not in cover_url:
                    cover_url = cover_url.replace('._AC_', '._AC_SL800_')
                cover_url = re.sub(r'_SX\d+_', '_SX800_', cover_url)
                logger.debug(f"✓ Cover image extracted with Playwright: {cover_url[:100]}...")
                return cover_url
        
        logger.warning("Cover image not found even with Playwright")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting cover image with Playwright: {e}", exc_info=True)
        return None


def extract_bsr_with_playwright_sync(amazon_url: str) -> Optional[int]:
    """
    Synchronous wrapper for extract_bsr_with_playwright
    For use in non-async contexts
    """
    try:
        logger.info(f"Starting synchronous BSR extraction for {amazon_url}")
        
        # Try to get existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run with timeout to prevent hanging
        logger.debug(f"Running async BSR extraction with 60s timeout")
        try:
            bsr = loop.run_until_complete(asyncio.wait_for(
                extract_bsr_with_playwright(amazon_url),
                timeout=60.0  # 60 second timeout
            ))
            logger.info(f"Synchronous BSR extraction completed: {bsr}")
            return bsr
        except asyncio.TimeoutError:
            logger.error(f"Timeout (60s) extracting BSR with Playwright for {amazon_url}")
            return None
        except Exception as e:
            logger.error(f"Error in synchronous BSR extraction: {e}", exc_info=True)
            return None
    except Exception as e:
        logger.error(f"Error setting up synchronous BSR extraction: {e}", exc_info=True)
        return None


def extract_cover_image_with_playwright_sync(amazon_url: str) -> Optional[str]:
    """
    Synchronous wrapper for extract_cover_image_with_playwright
    For use in non-async contexts
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(extract_cover_image_with_playwright(amazon_url))

