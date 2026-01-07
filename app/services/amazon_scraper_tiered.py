"""
Tiered Amazon Scraping Strategy
Tier 1: httpx/requests with caching
Tier 2: Playwright fallback
Tier 3: Mark as blocked with exponential backoff
"""
import logging
import time
import json
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import httpx
from bs4 import BeautifulSoup
import re

from app.services.browser_pool import fetch_page as playwright_fetch_page
from app.services.redis_cache import get_or_set, get_cache, set_cache

# Import strict BSR parser
try:
    from app.utils.bsr_parser import parse_bsr as strict_parse_bsr
    STRICT_BSR_PARSER_AVAILABLE = True
except ImportError:
    STRICT_BSR_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Structured logging for failures
FAILURE_LOG_FILE = 'amazon_scraping_failures.jsonl'


@dataclass
class ScrapingFailure:
    """Structured failure log entry"""
    timestamp: str
    url: str
    tier: int
    failure_type: str  # 'blocked', 'captcha', 'timeout', 'not_found', 'error'
    error_message: str
    page_length: Optional[int] = None
    page_snippet: Optional[str] = None
    retry_after: Optional[str] = None  # ISO timestamp for retry


class AmazonRobotDetector:
    """Detects Amazon robot check pages reliably"""
    
    # Patterns that indicate robot check pages
    ROBOT_INDICATORS = [
        r'robot.*check',
        r'captcha',
        r'verify.*you.*are.*human',
        r'sorry.*we.*just.*need.*verify',
        r'enter.*characters.*you.*see',
        r'access.*denied',
        r'blocked.*request',
        r'too.*many.*requests',
        r'rate.*limit',
    ]
    
    # Patterns that indicate normal Amazon pages
    NORMAL_PAGE_INDICATORS = [
        r'product.*details',
        r'add.*to.*cart',
        r'buy.*now',
        r'amazon.*best.*seller',
        r'customer.*reviews',
        r'product.*information',
    ]
    
    @staticmethod
    def is_robot_page(html: str) -> Tuple[bool, str]:
        """
        Detect if page is a robot check page
        
        Returns:
            (is_robot_page, reason)
        """
        if not html or len(html) < 1000:
            return True, "page_too_short"
        
        html_lower = html.lower()
        
        # Check for robot indicators
        for pattern in AmazonRobotDetector.ROBOT_INDICATORS:
            if re.search(pattern, html_lower, re.IGNORECASE):
                return True, f"robot_indicator: {pattern}"
        
        # Check for normal page indicators (if none found, might be blocked)
        has_normal_indicators = any(
            re.search(pattern, html_lower, re.IGNORECASE)
            for pattern in AmazonRobotDetector.NORMAL_PAGE_INDICATORS
        )
        
        # Very short pages without normal indicators are likely blocked
        if len(html) < 10000 and not has_normal_indicators:
            return True, "page_too_short_no_indicators"
        
        # Check for CAPTCHA forms
        if 'captcha' in html_lower and ('form' in html_lower or 'input' in html_lower):
            return True, "captcha_form_detected"
        
        # Check for Amazon error pages
        if 'sorry' in html_lower and 'amazon' in html_lower:
            if 'try again' in html_lower or 'refresh' in html_lower:
                return True, "amazon_error_page"
        
        return False, "normal_page"


class TieredAmazonScraper:
    """
    Tiered scraping strategy for Amazon pages
    """
    
    def __init__(self, cache_ttl: int = 3600, max_retry_delay: int = 86400):
        """
        Initialize tiered scraper
        
        Args:
            cache_ttl: Cache TTL in seconds (default: 1 hour)
            max_retry_delay: Maximum retry delay in seconds (default: 24 hours)
        """
        self.cache_ttl = cache_ttl
        self.max_retry_delay = max_retry_delay
        self.blocked_books: Dict[str, datetime] = {}  # URL -> retry_after timestamp
        
        # Realistic headers for Amazon
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.amazon.com/',
        }
        
        # httpx client with realistic settings
        self.client = httpx.Client(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
            http2=True,  # Use HTTP/2 for better performance
        )
    
    def _log_failure(self, failure: ScrapingFailure):
        """Log failure to structured log file"""
        try:
            with open(FAILURE_LOG_FILE, 'a') as f:
                f.write(json.dumps(asdict(failure)) + '\n')
        except Exception as e:
            logger.error(f"Failed to log failure: {e}")
    
    def _is_blocked(self, url: str) -> bool:
        """Check if URL is currently blocked"""
        if url not in self.blocked_books:
            return False
        
        retry_after = self.blocked_books[url]
        if datetime.now() < retry_after:
            return True
        
        # Retry time has passed, remove from blocked list
        del self.blocked_books[url]
        return False
    
    def _mark_blocked(self, url: str, retry_after: Optional[datetime] = None):
        """Mark URL as blocked with retry time"""
        if retry_after is None:
            # Exponential backoff: start with 1 hour, double each time
            last_retry = self.blocked_books.get(url, datetime.now() - timedelta(hours=1))
            hours_since_last = (datetime.now() - last_retry).total_seconds() / 3600
            retry_hours = min(2 ** int(hours_since_last), 24)  # Cap at 24 hours
            retry_after = datetime.now() + timedelta(hours=retry_hours)
        
        self.blocked_books[url] = retry_after
        logger.warning(f"Marked {url} as blocked until {retry_after.isoformat()}")
    
    def fetch_page_tier1(self, url: str) -> Optional[Tuple[str, bool]]:
        """
        Tier 1: httpx/requests with caching
        
        Returns:
            (html, is_blocked) or None if error
        """
        try:
            # Check cache first
            cached_html = self._get_cached_html(url)
            if cached_html:
                logger.debug(f"Cache hit for {url}")
                return cached_html, False
            
            # Check if blocked
            if self._is_blocked(url):
                logger.debug(f"Skipping {url} - currently blocked")
                return None, True
            
            # Add delay before request to avoid rate limiting
            try:
                import config
                delay = config.AMAZON_DELAY_BETWEEN_REQUESTS
            except (ImportError, AttributeError):
                delay = 5.0  # Default delay if config not available
            
            if delay > 0:
                time.sleep(delay)
            
            # Fetch with httpx
            response = self.client.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Detect robot pages
            is_robot, reason = AmazonRobotDetector.is_robot_page(html)
            
            if is_robot:
                logger.warning(f"Robot page detected for {url}: {reason}")
                self._log_failure(ScrapingFailure(
                    timestamp=datetime.now().isoformat(),
                    url=url,
                    tier=1,
                    failure_type='blocked',
                    error_message=reason,
                    page_length=len(html),
                    page_snippet=html[:500] if html else None
                ))
                return None, True
            
            # Cache successful fetch
            self._cache_html(url, html)
            
            return html, False
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning(f"403 Forbidden for {url}")
                self._log_failure(ScrapingFailure(
                    timestamp=datetime.now().isoformat(),
                    url=url,
                    tier=1,
                    failure_type='blocked',
                    error_message=f"HTTP 403: {str(e)}",
                ))
                return None, True
            logger.error(f"HTTP error for {url}: {e}")
            return None, False
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout for {url}: {e}")
            self._log_failure(ScrapingFailure(
                timestamp=datetime.now().isoformat(),
                url=url,
                tier=1,
                failure_type='timeout',
                error_message=str(e),
            ))
            return None, False
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self._log_failure(ScrapingFailure(
                timestamp=datetime.now().isoformat(),
                url=url,
                tier=1,
                failure_type='error',
                error_message=str(e),
            ))
            return None, False
    
    async def fetch_page_tier2(self, url: str) -> Optional[Tuple[str, bool]]:
        """
        Tier 2: Playwright fallback
        
        Returns:
            (html, is_blocked) or None if error
        """
        try:
            logger.info(f"Tier 2: Using Playwright for {url}")
            
            html = await playwright_fetch_page(url, timeout=30000, retries=2)
            
            if not html:
                return None, False
            
            # Detect robot pages
            is_robot, reason = AmazonRobotDetector.is_robot_page(html)
            
            if is_robot:
                logger.warning(f"Robot page detected with Playwright for {url}: {reason}")
                self._log_failure(ScrapingFailure(
                    timestamp=datetime.now().isoformat(),
                    url=url,
                    tier=2,
                    failure_type='blocked',
                    error_message=reason,
                    page_length=len(html),
                    page_snippet=html[:500] if html else None
                ))
                return None, True
            
            # Cache successful fetch
            self._cache_html(url, html)
            
            return html, False
            
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            self._log_failure(ScrapingFailure(
                timestamp=datetime.now().isoformat(),
                url=url,
                tier=2,
                failure_type='error',
                error_message=str(e),
            ))
            return None, False
    
    def fetch_page(self, url: str, use_playwright: bool = False) -> Optional[str]:
        """
        Main entry point: Try Tier 1, then Tier 2 if needed
        
        Args:
            url: URL to fetch
            use_playwright: If True, skip Tier 1 and go directly to Tier 2
            
        Returns:
            HTML content or None
        """
        import asyncio
        
        # Try Tier 1 first (unless explicitly requested to use Playwright)
        if not use_playwright:
            html, is_blocked = self.fetch_page_tier1(url)
            
            if html:
                return html
            
            if is_blocked:
                # Mark as blocked and return None
                self._mark_blocked(url)
                return None
        
        # Try Tier 2 (Playwright)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        html, is_blocked = loop.run_until_complete(self.fetch_page_tier2(url))
        
        if html:
            return html
        
        if is_blocked:
            # Mark as blocked for Tier 3
            self._mark_blocked(url)
            retry_after = self.blocked_books.get(url)
            self._log_failure(ScrapingFailure(
                timestamp=datetime.now().isoformat(),
                url=url,
                tier=3,
                failure_type='blocked',
                error_message="All tiers failed, marked for retry",
                retry_after=retry_after.isoformat() if retry_after else None
            ))
        
        return None
    
    def _get_cached_html(self, url: str) -> Optional[str]:
        """Get cached HTML from Redis"""
        cache_key = f"html:{url}"
        cached = get_cache(cache_key)
        if cached:
            logger.debug(f"Cache hit for HTML: {url[:50]}...")
        return cached
    
    def _cache_html(self, url: str, html: str):
        """Cache HTML content in Redis"""
        cache_key = f"html:{url}"
        # Cache HTML for 1 hour
        set_cache(cache_key, html, 3600)
        logger.debug(f"Cached HTML for: {url[:50]}...")
    
    def cleanup(self):
        """Cleanup resources"""
        self.client.close()


# Global instance
_tiered_scraper: Optional[TieredAmazonScraper] = None


def get_tiered_scraper() -> TieredAmazonScraper:
    """Get or create global tiered scraper instance"""
    global _tiered_scraper
    if _tiered_scraper is None:
        _tiered_scraper = TieredAmazonScraper()
    return _tiered_scraper

