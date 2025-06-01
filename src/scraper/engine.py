import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import stealth_async
import structlog
from src.core.config import settings
from src.models.scrape_config import ScrapeConfig

logger = structlog.get_logger()


class AntiDetectionManager:
    """Manages anti-detection strategies"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    
    @staticmethod
    async def setup_stealth(page: Page):
        """Apply stealth techniques to avoid detection"""
        await stealth_async(page)
        
        # Additional stealth measures
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
    
    @staticmethod
    def get_random_user_agent() -> str:
        import random
        return random.choice(AntiDetectionManager.USER_AGENTS)


class ProxyManager:
    """Manages proxy rotation"""
    
    def __init__(self):
        self.proxies: List[str] = []
        self.current_index = 0
    
    def add_proxy(self, proxy_url: str):
        """Add a proxy to the rotation pool"""
        self.proxies.append(proxy_url)
    
    def get_next_proxy(self) -> Optional[str]:
        """Get the next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy


class ScrapeEngine:
    """Main scraping engine with resilience and anti-detection"""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.browser: Optional[Browser] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with anti-detection
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
            ]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()
    
    async def create_context(self, config: ScrapeConfig) -> BrowserContext:
        """Create a new browser context with configuration"""
        context_options = {
            'user_agent': AntiDetectionManager.get_random_user_agent(),
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
        }
        
        # Add proxy if enabled
        if config.proxy_enabled and settings.proxy_enabled:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                context_options['proxy'] = {'server': proxy}
        
        return await self.browser.new_context(**context_options)
    
    async def extract_data(self, page: Page, css_selector: str) -> List[Dict[str, Any]]:
        """Extract data using CSS selector"""
        try:
            elements = await page.query_selector_all(css_selector)
            extracted_data = []
            
            for element in elements:
                # Get text content
                text_content = await element.text_content()
                
                # Get all attributes
                attributes = await element.evaluate('el => {const attrs = {}; for (let attr of el.attributes) { attrs[attr.name] = attr.value; } return attrs;}')
                
                # Get inner HTML
                inner_html = await element.inner_html()
                
                extracted_data.append({
                    'text': text_content.strip() if text_content else '',
                    'attributes': attributes,
                    'html': inner_html,
                    'tag_name': await element.evaluate('el => el.tagName.toLowerCase()')
                })
            
            return extracted_data
            
        except Exception as e:
            logger.error("Data extraction failed", selector=css_selector, error=str(e))
            return []
    
    async def wait_for_page_load(self, page: Page, wait_time: int):
        """Wait for page to fully load"""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Additional wait time as specified in config
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
        except Exception as e:
            logger.warning("Page load wait timeout", error=str(e))
    
    async def handle_captcha(self, page: Page) -> bool:
        """Basic CAPTCHA detection and handling"""
        try:
            # Look for common CAPTCHA indicators
            captcha_selectors = [
                '[data-captcha]',
                '.captcha',
                '#captcha',
                '.g-recaptcha',
                '.h-captcha',
                'iframe[src*="captcha"]',
                'iframe[src*="recaptcha"]'
            ]
            
            for selector in captcha_selectors:
                element = await page.query_selector(selector)
                if element:
                    logger.warning("CAPTCHA detected", selector=selector)
                    # For now, just return False. In production, integrate with CAPTCHA solving service
                    return False
            
            return True
            
        except Exception as e:
            logger.error("CAPTCHA handling failed", error=str(e))
            return False
    
    async def scrape_page(self, config: ScrapeConfig) -> Dict[str, Any]:
        """Scrape a single page based on configuration"""
        start_time = time.time()
        
        result = {
            'config_id': config.id,
            'status': 'failed',
            'raw_html': None,
            'extracted_data': None,
            'error_message': None,
            'started_at': datetime.utcnow(),
            'duration_seconds': None
        }
        
        context = None
        page = None
        
        try:
            # Create browser context
            context = await self.create_context(config)
            page = await context.new_page()
            
            # Apply stealth techniques
            await AntiDetectionManager.setup_stealth(page)
            
            # Set timeout
            page.set_default_timeout(config.timeout * 1000)
            
            logger.info("Starting scrape", url=config.start_url, config_id=config.id)
            
            # Navigate to the page
            response = await page.goto(config.start_url, wait_until='domcontentloaded')
            
            if not response or response.status >= 400:
                raise Exception(f"HTTP {response.status if response else 'No response'}")
            
            # Wait for page to load
            await self.wait_for_page_load(page, config.wait_time)
            
            # Check for CAPTCHA
            if not await self.handle_captcha(page):
                raise Exception("CAPTCHA detected and not solved")
            
            # Extract data
            extracted_data = await self.extract_data(page, config.css_selector)
            
            # Get raw HTML
            raw_html = await page.content()
            
            # Success
            result.update({
                'status': 'success',
                'raw_html': raw_html,
                'extracted_data': extracted_data,
                'duration_seconds': time.time() - start_time
            })
            
            logger.info("Scrape completed successfully", 
                       config_id=config.id, 
                       extracted_count=len(extracted_data))
            
        except Exception as e:
            error_msg = str(e)
            result.update({
                'status': 'failed',
                'error_message': error_msg,
                'duration_seconds': time.time() - start_time
            })
            
            logger.error("Scrape failed", 
                        config_id=config.id, 
                        url=config.start_url, 
                        error=error_msg)
        
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
        
        return result
    
    async def scrape_with_retries(self, config: ScrapeConfig) -> Dict[str, Any]:
        """Scrape with retry logic"""
        last_result = None
        
        for attempt in range(config.max_retries + 1):
            if attempt > 0:
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                logger.info("Retrying scrape", 
                           config_id=config.id, 
                           attempt=attempt, 
                           wait_time=wait_time)
                await asyncio.sleep(wait_time)
            
            result = await self.scrape_page(config)
            last_result = result
            
            if result['status'] == 'success':
                return result
            
            # Don't retry on certain errors
            if result.get('error_message'):
                error = result['error_message'].lower()
                if 'captcha' in error or '403' in error or '429' in error:
                    logger.info("Not retrying due to error type", error=error)
                    break
        
        return last_result