"""
Production-ready Playwright scraper with CAPTCHA handling and metrics
"""
import logging
import asyncio
from typing import Optional, Tuple
from bs4 import BeautifulSoup
import re

from app.services.browser_pool_refactored import fetch_page, CaptchaDetected
from app.services.scraper_metrics import get_metrics

try:
    from app.utils.bsr_parser import parse_bsr as strict_parse_bsr
    STRICT_BSR_PARSER_AVAILABLE = True
except ImportError:
    strict_parse_bsr = None
    STRICT_BSR_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


async def extract_bsr_with_playwright(amazon_url: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract BSR using Playwright with production-ready error handling
    
    Args:
        amazon_url: Amazon product URL
        
    Returns:
        Tuple of (bsr_value, error_reason)
        - If successful: (bsr_value, None)
        - If CAPTCHA: (None, "captcha")
        - If error: (None, error_reason)
    """
    metrics = get_metrics()
    
    # Clean URL
    clean_url = amazon_url.split('/ref')[0].split('?')[0].rstrip('/')
    if not clean_url.endswith('/'):
        clean_url += '/'
    
    try:
        logger.debug(f"Fetching page with Playwright for BSR: {clean_url}")
        html, error_reason = await fetch_page(clean_url, timeout=30000)
        
        if error_reason == "captcha":
            # CAPTCHA detected - abort immediately, do not retry
            logger.warning(f"CAPTCHA detected for {clean_url} - aborting extraction")
            return None, "captcha"
        
        if error_reason == "screenshot_saved":
            # Screenshot saved - stop scraping for OCR processing
            logger.info(f"Screenshot saved for {clean_url} - stopping scraping for OCR processing")
            return None, "screenshot_saved"
        
        if not html:
            logger.warning(f"Failed to fetch page: {error_reason}")
            return None, error_reason
        
        # Extract BSR using strict parser
        if STRICT_BSR_PARSER_AVAILABLE:
            bsr = strict_parse_bsr(html)
            if bsr:
                logger.info(f"✅ BSR extracted: #{bsr:,}")
                return bsr, None
            else:
                logger.warning(f"BSR not found in HTML for {clean_url}")
                return None, "bsr_not_found"
        else:
            # Fallback parser
            soup = BeautifulSoup(html, 'lxml')
            page_text = soup.get_text()
            
            patterns = [
                r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
                r'Best\s+Sellers\s+Rank[:\s]*#?(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        bsr_value = int(match.group(1).replace(',', ''))
                        if 1 <= bsr_value < 10000000:
                            logger.info(f"✅ BSR extracted: #{bsr_value:,}")
                            return bsr_value, None
                    except:
                        continue
            
            logger.warning(f"BSR not found for {clean_url}")
            return None, "bsr_not_found"
    
    except CaptchaDetected:
        logger.warning(f"CAPTCHA detected for {clean_url} - aborting")
        return None, "captcha"
    
    except Exception as e:
        logger.error(f"Error extracting BSR: {e}", exc_info=True)
        return None, str(e)


def extract_bsr_with_playwright_sync(amazon_url: str) -> Optional[int]:
    """
    Synchronous wrapper for extract_bsr_with_playwright
    Returns only BSR value (None if error or CAPTCHA)
    """
    try:
        logger.info(f"Starting BSR extraction for {amazon_url}")
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            bsr, error_reason = loop.run_until_complete(asyncio.wait_for(
                extract_bsr_with_playwright(amazon_url),
                timeout=120.0  # 2 minute timeout
            ))
            
            if error_reason == "captcha":
                logger.warning(f"CAPTCHA detected - returning None (reason: {error_reason})")
                return None
            
            logger.info(f"BSR extraction completed: {bsr}")
            return bsr
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout extracting BSR for {amazon_url}")
            return None
        except Exception as e:
            logger.error(f"Error in synchronous BSR extraction: {e}", exc_info=True)
            return None
    
    except Exception as e:
        logger.error(f"Error setting up synchronous BSR extraction: {e}", exc_info=True)
        return None

