"""
Production-ready Playwright Browser Pool Service
Optimized for stealth, stability, and low memory usage
"""
import logging
import asyncio
import random
import re
import json
import time
from typing import Optional, Tuple
from contextlib import asynccontextmanager
from threading import Lock
from pathlib import Path
import os

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from app.services.scraper_metrics import get_metrics

logger = logging.getLogger(__name__)


class CaptchaDetected(Exception):
    """Exception raised when CAPTCHA is detected - should abort immediately"""
    pass


class BrowserPool:
    """
    Production-ready browser pool with stealth optimizations
    - Single browser instance (no parallel scraping)
    - Persistent session storage
    - CAPTCHA detection with immediate abort
    - Exponential backoff for errors
    - Metrics tracking
    """
    
    def __init__(self, headless: Optional[bool] = None):
        """
        Initialize browser pool
        
        Args:
            headless: Run browser in headless mode (None = auto-detect from env)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        
        # Auto-detect from environment variable if not specified
        if headless is None:
            headless_env = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower()
            self.headless = headless_env not in ['false', '0', 'no', 'off']
        else:
            self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._lock = Lock()
        self._initialized = False
        self._init_lock = None
        self._initializing = False
        
        # Storage state path for session persistence
        storage_dir = Path(os.getenv('PLAYWRIGHT_STORAGE_DIR', '/tmp/playwright_storage'))
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_state_path = storage_dir / 'amazon_session.json'
        
        # Metrics
        self.metrics = get_metrics()
    
    async def initialize(self):
        """Initialize browser (thread-safe, single browser only)"""
        if self._init_lock is None:
            try:
                self._init_lock = asyncio.Lock()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            if self._initialized:
                return
            
            if self._initializing:
                while self._initializing:
                    await asyncio.sleep(0.1)
                if self._initialized:
                    return
            
            self._initializing = True
            
            try:
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
                        proxy_url = config.AMAZON_PROXY
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
                        logger.info(f"Using proxy: {proxy_config.get('server', 'N/A')}")
                except Exception as e:
                    logger.debug(f"Could not configure proxy: {e}")
                
                # Launch single browser
                launch_options = {
                    'headless': self.headless,
                    'args': [
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                }
                
                if proxy_config:
                    launch_options['proxy'] = proxy_config
                
                self.browser = await self.playwright.chromium.launch(**launch_options)
                
                # Load storage state if exists (persist session)
                storage_state = None
                if self.storage_state_path.exists():
                    try:
                        with open(self.storage_state_path, 'r') as f:
                            storage_state = json.load(f)
                        logger.debug("Loaded existing storage state for session persistence")
                    except Exception as e:
                        logger.debug(f"Could not load storage state: {e}")
                
                # Create context with realistic settings
                context_options = {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'locale': 'en-US',
                    'timezone_id': 'America/New_York',
                    'permissions': ['geolocation'],
                    'ignore_https_errors': False,
                    'java_script_enabled': True,
                    'bypass_csp': True,
                    'extra_http_headers': {
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0',
                        'DNT': '1',
                    }
                }
                
                if storage_state:
                    context_options['storage_state'] = storage_state
                
                self.context = await self.browser.new_context(**context_options)
                
                # Add comprehensive stealth scripts
                await self.context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    delete navigator.__proto__.webdriver;
                    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                    Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
                    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
                    Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
                    Object.defineProperty(navigator, 'connection', {
                        get: () => ({ effectiveType: '4g', rtt: 50, downlink: 10, saveData: false })
                    });
                """)
                
                self._initialized = True
                logger.info("Browser pool initialized (single browser)")
            
            except Exception as e:
                self._initializing = False
                logger.error(f"Failed to initialize browser pool: {e}", exc_info=True)
                await self.cleanup()
                raise
    
    @asynccontextmanager
    async def get_context(self):
        """Get browser context (always returns the same context)"""
        if not self._initialized:
            await self.initialize()
        
        yield self.context
    
    def _detect_captcha(self, html: str) -> bool:
        """
        Detect CAPTCHA in HTML
        
        Returns:
            True if CAPTCHA is detected
        """
        html_lower = html.lower()
        captcha_patterns = [
            r'captcha.*form',
            r'enter.*characters.*you.*see',
            r'type.*characters.*below',
            r'amazon.*robot.*check',
            r'verify.*you.*are.*human',
            r'sorry.*we.*just.*need.*verify',
            r'we.*detected.*unusual.*traffic'
        ]
        
        return any(re.search(pattern, html_lower, re.IGNORECASE) for pattern in captcha_patterns)
    
    def _is_network_error(self, error: Exception) -> bool:
        """Check if error is a network error (retryable)"""
        error_str = str(error).lower()
        network_indicators = ['timeout', 'connection', 'network', 'reset', 'refused', 'econnreset']
        return any(indicator in error_str for indicator in network_indicators)
    
    async def _save_storage_state(self):
        """Save browser storage state for session persistence"""
        try:
            if self.context:
                storage_state = await self.context.storage_state()
                with open(self.storage_state_path, 'w') as f:
                    json.dump(storage_state, f)
                logger.debug("Saved storage state")
        except Exception as e:
            logger.debug(f"Could not save storage state: {e}")
    
    async def fetch_page(self, url: str, timeout: int = 30000) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch page HTML with production-ready error handling
        
        Args:
            url: URL to fetch
            timeout: Timeout in milliseconds
            
        Returns:
            Tuple of (html, error_reason)
            - If successful: (html, None)
            - If CAPTCHA: (None, "captcha")
            - If network error: (None, "network_error")
            - If other error: (None, error_message)
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        retried = False
        
        try:
            async with self.get_context() as context:
                page = await context.new_page()
                
                try:
                    # Random delay: 45-120 seconds (or from env for testing)
                    # Check environment variables FIRST (for local testing)
                    env_delay_min = os.getenv('AMAZON_DELAY_MIN')
                    env_delay_max = os.getenv('AMAZON_DELAY_MAX')
                    
                    if env_delay_min and env_delay_max:
                        # Use environment variables if set (for testing)
                        delay_min = float(env_delay_min)
                        delay_max = float(env_delay_max)
                        logger.info(f"Using test delays from environment: {delay_min}-{delay_max}s")
                    else:
                        # Use config defaults
                        try:
                            import config
                            delay_min = getattr(config, 'AMAZON_DELAY_MIN', 45)
                            delay_max = getattr(config, 'AMAZON_DELAY_MAX', 120)
                        except:
                            delay_min = 45
                            delay_max = 120
                    
                    delay = random.uniform(delay_min, delay_max)
                    logger.info(f"⏳ Waiting {delay:.1f}s before navigation to {url}")
                    await asyncio.sleep(delay)
                    
                    logger.info(f"🌐 Navigating to {url}...")
                    
                    # Navigate with exponential backoff for 500/503
                    max_retries = 3
                    backoff_delays = [60, 180, 600]  # 1 min, 3 min, 10 min
                    
                    response = None
                    for retry_attempt in range(max_retries):
                        try:
                            logger.info(f"📡 Attempting to navigate to {url} (attempt {retry_attempt + 1}/{max_retries})")
                            response = await page.goto(
                                url,
                                wait_until='networkidle',
                                timeout=timeout
                            )
                            logger.info(f"✅ Navigation successful, status: {response.status if response else 'N/A'}")
                            
                            # Check for 500/503 errors
                            if response and response.status in [500, 503]:
                                if retry_attempt < len(backoff_delays):
                                    backoff = backoff_delays[retry_attempt]
                                    logger.warning(f"Received {response.status} error, applying {backoff}s backoff (attempt {retry_attempt + 1}/{max_retries})")
                                    await asyncio.sleep(backoff)
                                    continue
                                else:
                                    logger.error(f"Received {response.status} error after {max_retries} attempts")
                                    raise Exception(f"HTTP {response.status} after {max_retries} retries")
                            else:
                                break  # Success or other status code
                        
                        except PlaywrightTimeoutError:
                            if retry_attempt < max_retries - 1:
                                backoff = backoff_delays[retry_attempt] if retry_attempt < len(backoff_delays) else 600
                                logger.warning(f"Timeout, retrying after {backoff}s (attempt {retry_attempt + 1}/{max_retries})")
                                await asyncio.sleep(backoff)
                                retried = True
                                continue
                            else:
                                raise
                    
                    # Check for "Continue shopping" interstitial page and handle it
                    await page.wait_for_timeout(2000)  # Wait for page to fully load
                    page_content = await page.content()
                    page_text = await page.inner_text('body')
                    
                    # Detect "Continue shopping" interstitial page
                    if 'continue shopping' in page_text.lower() or 'click the button below to continue' in page_text.lower():
                        logger.warning("⚠️  Detected 'Continue shopping' interstitial page - attempting to click button")
                        try:
                            # Try multiple selectors for the continue button
                            button_selectors = [
                                'button:has-text("Continue shopping")',
                                'a:has-text("Continue shopping")',
                                'input[value*="Continue"]',
                                'button[type="submit"]',
                                '.a-button-primary:has-text("Continue")',
                            ]
                            
                            clicked = False
                            for selector in button_selectors:
                                try:
                                    button = await page.query_selector(selector)
                                    if button:
                                        logger.info(f"Clicking 'Continue shopping' button (selector: {selector})")
                                        await button.click()
                                        await page.wait_for_timeout(3000)  # Wait for redirect
                                        clicked = True
                                        break
                                except Exception as e:
                                    logger.debug(f"Selector {selector} failed: {e}")
                                    continue
                            
                            if not clicked:
                                # Try clicking by text content
                                try:
                                    await page.click('text=Continue shopping', timeout=5000)
                                    await page.wait_for_timeout(3000)
                                    clicked = True
                                    logger.info("Clicked 'Continue shopping' by text")
                                except:
                                    pass
                            
                            if clicked:
                                # Wait for navigation after click
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                logger.info("✅ Successfully clicked 'Continue shopping' - page should redirect")
                            else:
                                logger.warning("Could not find/click 'Continue shopping' button")
                        except Exception as e:
                            logger.warning(f"Error handling 'Continue shopping' page: {e}")
                    
                    # Re-check page content after handling interstitial
                    page_content = await page.content()
                    page_text = await page.inner_text('body')
                    
                    # Check again if we're still on interstitial page after click
                    if 'continue shopping' in page_text.lower() and 'click the button below' in page_text.lower():
                        # Still on interstitial - this is likely a blocking page
                        logger.warning("Still on 'Continue shopping' page after click - likely blocked")
                        duration = time.time() - start_time
                        self.metrics.record_request(duration, success=False, error_reason="continue_shopping_interstitial")
                        await self._save_storage_state()
                        return None, "continue_shopping_interstitial"
                    
                    # Human-like behavior
                    await page.wait_for_timeout(random.uniform(2000, 4000))
                    await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                    await page.wait_for_timeout(random.uniform(500, 1000))
                    
                    # Scroll gradually to find "See all details" section
                    scroll_positions = [0.2, 0.4, 0.6, 0.8, 1.0]
                    for pos in scroll_positions:
                        scroll_y = await page.evaluate(f"Math.floor(document.body.scrollHeight * {pos})")
                        await page.evaluate(f"window.scrollTo({{top: {scroll_y}, behavior: 'smooth'}})")
                        await page.wait_for_timeout(random.uniform(1000, 2000))
                        
                        # Try to find and click "See all details" link
                        try:
                            # Multiple selectors for "See all details" link
                            see_all_selectors = [
                                '#rich_product_information-learn_more_link',
                                'a[href*="detailBullets_feature_div"]',
                                'a:has-text("See all details")',
                                'a:has-text("see all details")',
                                '.a-link-normal:has-text("See all details")',
                            ]
                            
                            clicked = False
                            for selector in see_all_selectors:
                                try:
                                    element = await page.query_selector(selector)
                                    if element:
                                        # Check if element is visible
                                        is_visible = await element.is_visible()
                                        if is_visible:
                                            logger.info(f"Found 'See all details' link - clicking (selector: {selector})")
                                            # Scroll element into view
                                            await element.scroll_into_view_if_needed()
                                            await page.wait_for_timeout(random.uniform(500, 1000))
                                            # Click with human-like delay
                                            await element.click(timeout=5000)
                                            await page.wait_for_timeout(random.uniform(2000, 3000))  # Wait for content to load
                                            clicked = True
                                            logger.info("✅ Successfully clicked 'See all details'")
                                            break
                                except Exception as e:
                                    logger.debug(f"Selector {selector} failed: {e}")
                                    continue
                            
                            if clicked:
                                # Wait a bit more for the expanded content to load
                                await page.wait_for_timeout(random.uniform(1000, 2000))
                                break  # Found and clicked, no need to continue scrolling
                        except Exception as e:
                            logger.debug(f"Error looking for 'See all details': {e}")
                            continue
                    
                    # Final wait after all scrolling/interactions
                    await page.wait_for_timeout(random.uniform(2000, 4000))
                    
                    # Get HTML (now with expanded "See all details" content)
                    html = await page.content()
                    
                    # Check for CAPTCHA - IMMEDIATE ABORT
                    if self._detect_captcha(html):
                        duration = time.time() - start_time
                        logger.warning(f"CAPTCHA detected for {url} - aborting immediately")
                        self.metrics.record_request(duration, success=False, captcha=True, error_reason="captcha")
                        await self._save_storage_state()
                        raise CaptchaDetected("CAPTCHA detected")
                    
                    # Success
                    duration = time.time() - start_time
                    self.metrics.record_request(duration, success=True)
                    await self._save_storage_state()
                    return html, None
                
                finally:
                    await page.close()
        
        except CaptchaDetected:
            # CAPTCHA - do not retry, abort immediately
            duration = time.time() - start_time
            self.metrics.record_request(duration, success=False, captcha=True, error_reason="captcha")
            return None, "captcha"
        
        except (PlaywrightTimeoutError, asyncio.TimeoutError) as e:
            # Timeout - network error, could retry but we don't here
            duration = time.time() - start_time
            error_reason = "timeout"
            self.metrics.record_request(duration, success=False, retried=retried, error_reason=error_reason)
            logger.warning(f"Timeout fetching {url}: {e}")
            return None, error_reason
        
        except Exception as e:
            # Other errors
            duration = time.time() - start_time
            error_reason = str(e)
            is_network = self._is_network_error(e)
            
            if is_network:
                error_reason = "network_error"
            
            self.metrics.record_request(duration, success=False, retried=retried, error_reason=error_reason)
            logger.error(f"Error fetching {url}: {e}")
            return None, error_reason
    
    async def cleanup(self):
        """Cleanup browser resources"""
        with self._lock:
            if self._initialized:
                try:
                    if self.context:
                        await self._save_storage_state()
                        await self.context.close()
                        self.context = None
                    if self.browser:
                        await self.browser.close()
                        self.browser = None
                    if self.playwright:
                        await self.playwright.stop()
                        self.playwright = None
                    self._initialized = False
                    logger.info("Browser pool cleaned up")
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")


# Global pool instance (singleton)
_pool: Optional[BrowserPool] = None
_pool_lock = Lock()


async def get_browser_pool(headless: Optional[bool] = None) -> BrowserPool:
    """Get global browser pool instance (singleton)"""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = BrowserPool(headless=headless)
    return _pool


async def fetch_page(url: str, timeout: int = 30000) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch page using global browser pool
    
    Returns:
        Tuple of (html, error_reason)
    """
    pool = await get_browser_pool()
    return await pool.fetch_page(url, timeout)

