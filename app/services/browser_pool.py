"""
Playwright Browser Pool Service
Manages a pool of reusable browser contexts for efficient scraping
"""
import logging
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager
from threading import Lock
import time

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")

logger = logging.getLogger(__name__)


class BrowserPool:
    """
    Browser pool that reuses contexts instead of spawning new ones
    Maintains 1-3 browsers with reusable contexts
    """
    
    def __init__(self, pool_size: int = 2, headless: bool = True):
        """
        Initialize browser pool
        
        Args:
            pool_size: Number of browsers in pool (1-3)
            headless: Run browsers in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Install with: pip install playwright && playwright install chromium")
        
        self.pool_size = max(1, min(3, pool_size))  # Clamp between 1 and 3
        self.headless = headless
        self.playwright = None
        self.browsers: List[Browser] = []
        self.contexts: List[BrowserContext] = []
        self.context_lock = Lock()
        self._initialized = False
        self._cleanup_lock = Lock()
        
    async def initialize(self):
        """Initialize browser pool"""
        if self._initialized:
            return
        
        try:
            self.playwright = await async_playwright().start()
            
            # Create browsers
            for i in range(self.pool_size):
                browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                    ]
                )
                
                # Create context with realistic settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                # Add stealth scripts to avoid detection
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                """)
                
                self.browsers.append(browser)
                self.contexts.append(context)
                logger.info(f"Initialized browser {i+1}/{self.pool_size}")
            
            self._initialized = True
            logger.info(f"Browser pool initialized with {self.pool_size} browsers")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser pool: {e}", exc_info=True)
            await self.cleanup()
            raise
    
    @asynccontextmanager
    async def get_context(self):
        """
        Get a browser context from the pool (context manager)
        Automatically returns context to pool after use
        Creates new context if pool is exhausted
        """
        if not self._initialized:
            await self.initialize()
        
        context = None
        created_new = False
        try:
            # Get next available context (round-robin)
            with self.context_lock:
                if not self.contexts:
                    # Pool exhausted - create a new temporary context
                    logger.warning("Browser pool exhausted, creating temporary context")
                    if self.browsers:
                        browser = self.browsers[0]  # Use first browser
                        context = await browser.new_context(
                            viewport={'width': 1920, 'height': 1080},
                            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            locale='en-US',
                            timezone_id='America/New_York',
                        )
                        created_new = True
                    else:
                        raise RuntimeError("No browser contexts available and no browsers to create new context")
                else:
                    context = self.contexts.pop(0)
            
            yield context
            
        finally:
            # Return context to pool (or close if temporary)
            if context:
                with self.context_lock:
                    if created_new:
                        # Close temporary context instead of returning to pool
                        try:
                            await context.close()
                        except Exception as e:
                            logger.warning(f"Error closing temporary context: {e}")
                    else:
                        # Return to pool
                        self.contexts.append(context)
    
    async def fetch_page(self, url: str, timeout: int = 30000, retries: int = 3, wait_until: str = 'domcontentloaded') -> Optional[str]:
        """
        Fetch page HTML using browser pool
        
        Args:
            url: URL to fetch
            timeout: Timeout in milliseconds
            retries: Number of retry attempts
            wait_until: When to consider navigation successful ('load', 'domcontentloaded', 'networkidle')
            
        Returns:
            HTML content as string, or None if failed
        """
        if not self._initialized:
            await self.initialize()
        
        last_error = None
        
        for attempt in range(retries):
            try:
                async with self.get_context() as context:
                    page = await context.new_page()
                    
                    try:
                        # Navigate to page
                        await page.goto(
                            url,
                            wait_until=wait_until,
                            timeout=timeout
                        )
                        
                        # Wait a bit for dynamic content
                        await page.wait_for_timeout(2000)
                        
                        # Scroll to trigger lazy loading
                        await page.evaluate("""
                            window.scrollTo(0, document.body.scrollHeight / 2);
                        """)
                        await page.wait_for_timeout(1000)
                        
                        # Get page content
                        html = await page.content()
                        
                        # Check if page is blocked (CAPTCHA, etc.)
                        if len(html) < 10000:
                            logger.warning(f"Page appears to be blocked (length: {len(html)} chars)")
                            raise Exception("Page appears to be blocked")
                        
                        if 'captcha' in html.lower() and 'verify' in html.lower():
                            logger.warning("CAPTCHA detected on page")
                            raise Exception("CAPTCHA detected")
                        
                        logger.debug(f"Successfully fetched page: {url} (attempt {attempt + 1})")
                        return html
                        
                    finally:
                        await page.close()
                        
            except PlaywrightTimeoutError as e:
                last_error = e
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to fetch {url} after {retries} attempts: {last_error}")
        return None
    
    async def cleanup(self):
        """Cleanup all browsers and contexts"""
        with self._cleanup_lock:
            if not self._initialized:
                return
            
            try:
                # Close all contexts
                for context in self.contexts:
                    try:
                        await context.close()
                    except Exception as e:
                        logger.warning(f"Error closing context: {e}")
                
                # Close all browsers
                for browser in self.browsers:
                    try:
                        await browser.close()
                    except Exception as e:
                        logger.warning(f"Error closing browser: {e}")
                
                # Stop playwright
                if self.playwright:
                    try:
                        await self.playwright.stop()
                    except Exception as e:
                        logger.warning(f"Error stopping playwright: {e}")
                
                self.browsers.clear()
                self.contexts.clear()
                self._initialized = False
                logger.info("Browser pool cleaned up")
                
            except Exception as e:
                logger.error(f"Error during browser pool cleanup: {e}", exc_info=True)


# Global browser pool instance
_browser_pool: Optional[BrowserPool] = None
_pool_lock = Lock()


def get_browser_pool(pool_size: int = 2, headless: bool = True) -> BrowserPool:
    """Get or create global browser pool instance"""
    global _browser_pool
    
    if _browser_pool is None:
        with _pool_lock:
            if _browser_pool is None:
                _browser_pool = BrowserPool(pool_size=pool_size, headless=headless)
    
    return _browser_pool


async def fetch_page(url: str, timeout: int = 30000, retries: int = 3) -> Optional[str]:
    """
    Fetch page HTML using browser pool (convenience function)
    
    Args:
        url: URL to fetch
        timeout: Timeout in milliseconds
        retries: Number of retry attempts
        
    Returns:
        HTML content as string, or None if failed
    """
    pool = get_browser_pool()
    return await pool.fetch_page(url, timeout=timeout, retries=retries)


async def cleanup_browser_pool():
    """Cleanup global browser pool"""
    global _browser_pool
    if _browser_pool:
        await _browser_pool.cleanup()
        _browser_pool = None

