"""
Playwright Browser Pool Service
Manages a pool of reusable browser contexts for efficient scraping
"""
import logging
import asyncio
import random
import re
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
        self._init_lock = None  # Will be created as async lock when needed
        self._initializing = False
        
    async def initialize(self):
        """Initialize browser pool (thread-safe)"""
        # Use async lock to prevent concurrent initialization
        if self._init_lock is None:
            try:
                self._init_lock = asyncio.Lock()
            except RuntimeError:
                # No event loop in this thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            if self._initialized:
                return
            
            if self._initializing:
                # Wait for other thread to finish initialization
                while self._initializing:
                    await asyncio.sleep(0.1)
                if self._initialized:
                    return
            
            self._initializing = True
            
            try:
                # Ensure we're using the current event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                
                self.playwright = await async_playwright().start()
                
                # Configure proxy if available
                proxy_config = None
                try:
                    import config
                    if config.AMAZON_USE_PROXY and config.AMAZON_PROXY:
                        # Parse proxy URL
                        proxy_url = config.AMAZON_PROXY
                        if proxy_url.startswith('http://') or proxy_url.startswith('https://'):
                            # Extract user:pass@host:port if present
                            if '@' in proxy_url:
                                auth_part, server_part = proxy_url.split('@')
                                if '://' in auth_part:
                                    protocol = auth_part.split('://')[0] + '://'
                                    auth = auth_part.split('://')[1]
                                    if ':' in auth:
                                        username, password = auth.split(':', 1)
                                        proxy_config = {
                                            'server': protocol + server_part,
                                            'username': username,
                                            'password': password
                                        }
                                    else:
                                        proxy_config = {'server': proxy_url}
                                else:
                                    proxy_config = {'server': proxy_url}
                            else:
                                proxy_config = {'server': proxy_url}
                        logger.info(f"Using proxy for Playwright: {proxy_config.get('server', 'N/A')}")
                except Exception as e:
                    logger.debug(f"Could not configure proxy: {e}")
                
                # Create browsers sequentially to avoid event loop conflicts
                for i in range(self.pool_size):
                    launch_options = {
                        'headless': self.headless,
                        'args': [
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                        ]
                    }
                    
                    # Add proxy if configured
                    if proxy_config:
                        launch_options['proxy'] = proxy_config
                    
                    browser = await self.playwright.chromium.launch(**launch_options)
                    
                    # Create context with realistic settings
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='en-US',
                        timezone_id='America/New_York',
                        permissions=['geolocation'],
                        # Disable automation indicators
                        ignore_https_errors=False,
                        java_script_enabled=True,
                        bypass_csp=True,
                        extra_http_headers={
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Sec-Fetch-User': '?1',
                            'Cache-Control': 'max-age=0',
                            'DNT': '1',
                        }
                    )
                
                # Add comprehensive stealth scripts to avoid detection
                await context.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Remove automation indicators
                    delete navigator.__proto__.webdriver;
                    
                    // Add chrome object
                    window.chrome = { 
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // Override plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Override permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Override getBattery
                    Object.defineProperty(navigator, 'getBattery', {
                        get: () => () => Promise.resolve({
                            charging: true,
                            chargingTime: 0,
                            dischargingTime: Infinity,
                            level: 1
                        })
                    });
                    
                    // Override platform
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'MacIntel'
                    });
                    
                    // Override hardwareConcurrency
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8
                    });
                    
                    // Override deviceMemory
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => 8
                    });
                    
                    // Override vendor
                    Object.defineProperty(navigator, 'vendor', {
                        get: () => 'Google Inc.'
                    });
                    
                    // Override connection
                    Object.defineProperty(navigator, 'connection', {
                        get: () => ({
                            effectiveType: '4g',
                            rtt: 50,
                            downlink: 10,
                            saveData: false
                        })
                    });
                    
                    // Override canvas fingerprinting
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function(type) {
                        if (type === 'image/png' || type === 'image/jpeg') {
                            return originalToDataURL.apply(this, arguments);
                        }
                        return originalToDataURL.apply(this, arguments);
                    };
                    
                    // Override WebGL fingerprinting
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.apply(this, arguments);
                    };
                    """)
                
                self.browsers.append(browser)
                self.contexts.append(context)
                logger.info(f"Initialized browser {i+1}/{self.pool_size}")
                
                self._initialized = True
                self._initializing = False
                logger.info(f"Browser pool initialized with {self.pool_size} browsers")
            
            except Exception as e:
                self._initializing = False
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
                        # Add longer random delay before navigation (5-10 seconds) to avoid detection
                        await asyncio.sleep(random.uniform(5, 10))
                        
                        # Navigate to page with networkidle for better stealth
                        await page.goto(
                            url,
                            wait_until='networkidle',
                            timeout=timeout
                        )
                        
                        # Wait longer for dynamic content and to appear more human-like
                        await page.wait_for_timeout(random.uniform(3000, 6000))
                        
                        # Simulate mouse movement (human-like behavior)
                        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                        await page.wait_for_timeout(random.uniform(500, 1000))
                        
                        # Human-like scrolling with mouse movements
                        scroll_positions = [0.2, 0.4, 0.6, 0.8, 1.0]
                        for pos in scroll_positions:
                            # Scroll gradually - get scroll height first, then scroll
                            scroll_y = await page.evaluate(f"""
                                () => {{
                                    return Math.floor(document.body.scrollHeight * {pos});
                                }}
                            """)
                            await page.evaluate(f"""
                                window.scrollTo({{
                                    top: {scroll_y},
                                    behavior: 'smooth'
                                }});
                            """)
                            # Random mouse movement during scroll
                            await page.mouse.move(
                                random.randint(200, 800),
                                random.randint(200, 600)
                            )
                            await page.wait_for_timeout(random.uniform(1000, 2500))
                        
                        # Final wait to appear more human
                        await page.wait_for_timeout(random.uniform(2000, 4000))
                        
                        # Get page content
                        html = await page.content()
                        html_lower = html.lower()
                        
                        # IMPORTANT: Try to extract BSR even if page appears blocked
                        # Sometimes BSR is still in HTML even with CAPTCHA
                        bsr_found = False
                        try:
                            from app.utils.bsr_parser import parse_bsr
                            bsr_value = parse_bsr(html)
                            if bsr_value:
                                logger.info(f"✅ BSR found in HTML: #{bsr_value:,}")
                                bsr_found = True
                                # Return HTML anyway - BSR parser will extract it
                        except Exception as e:
                            logger.debug(f"Could not parse BSR from HTML: {e}")
                        
                        # Check for blocking indicators (more sophisticated)
                        is_blocked = False
                        block_reason = None
                        
                        # More precise CAPTCHA detection - look for actual CAPTCHA pages, not just mentions
                        # CAPTCHA pages usually have specific patterns
                        captcha_indicators = [
                            r'captcha.*form',
                            r'enter.*characters.*you.*see',
                            r'type.*characters.*below',
                            r'amazon.*robot.*check',
                            r'verify.*you.*are.*human',
                            r'sorry.*we.*just.*need.*verify'
                        ]
                        has_captcha_page = any(
                            re.search(pattern, html_lower, re.IGNORECASE)
                            for pattern in captcha_indicators
                        )
                        
                        # Check for normal page indicators (more comprehensive)
                        normal_indicators = [
                            r'product.*details',
                            r'add.*to.*cart',
                            r'buy.*now',
                            r'amazon.*best.*seller',
                            r'customer.*reviews',
                            r'product.*information',
                            r'best sellers rank',
                            r'#.*in.*books',
                            r'salesrank',
                            r'kindle.*store',
                            r'product.*title',
                            r'by.*author',
                            r'price.*\$',
                            r'product.*description',
                            r'asin',
                            r'isbn'
                        ]
                        has_normal_indicators = any(
                            re.search(pattern, html_lower, re.IGNORECASE)
                            for pattern in normal_indicators
                        )
                        
                        # Count normal indicators to be more lenient
                        normal_count = sum(
                            1 for pattern in normal_indicators
                            if re.search(pattern, html_lower, re.IGNORECASE)
                        )
                        
                        # If BSR was found, always return HTML (even with CAPTCHA)
                        if bsr_found:
                            logger.info("BSR found - returning HTML despite potential CAPTCHA")
                            # Don't raise exception - return HTML so BSR can be extracted
                        # Be more permissive: if page has substantial content (5000+ chars), allow extraction
                        # even with CAPTCHA - BSR might be in HTML in a different format
                        elif has_captcha_page and normal_count < 3 and len(html) < 5000:
                            # Only block if it's clearly a CAPTCHA page with minimal content (< 5000 chars)
                            # Pages with 5000+ chars might still have BSR even with CAPTCHA
                            is_blocked = True
                            block_reason = f"CAPTCHA page detected (normal indicators: {normal_count}, length: {len(html)})"
                        elif len(html) < 1500:
                            # Very short pages are likely blocked (but allow if BSR found)
                            is_blocked = True
                            block_reason = f"Page very short ({len(html)} chars)"
                        elif has_captcha_page and len(html) >= 5000:
                            # Page has substantial content (5000+ chars) - allow extraction even with CAPTCHA
                            # BSR might be present in HTML in a format parser doesn't recognize yet
                            logger.info(f"CAPTCHA detected but page has {len(html)} chars - allowing extraction (normal indicators: {normal_count})")
                            # Don't block - return HTML for BSR extraction
                        
                        if is_blocked and not bsr_found:
                            logger.warning(f"Page appears to be blocked: {block_reason}")
                            raise Exception(f"Page appears to be blocked: {block_reason}")
                        elif has_captcha_page and bsr_found:
                            logger.info(f"CAPTCHA detected but BSR found - proceeding with extraction")
                        elif has_captcha_page and normal_count >= 3:
                            logger.info(f"CAPTCHA detected but page has {normal_count} normal indicators - proceeding")
                        elif has_captcha_page and len(html) >= 5000:
                            logger.info(f"CAPTCHA detected but page has {len(html)} chars - allowing extraction attempt")
                        
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

