import os
import sys
import platform
import logging
import httpx
import asyncio
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger()

# Detect platform
is_windows = platform.system() == 'Windows'
is_python_312_plus = sys.version_info >= (3, 12)

logger.info(f"Platform: {platform.system()}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Is Windows: {is_windows}")
logger.info(f"Is Python 3.12+: {is_python_312_plus}")

# Setup HTTP client
limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
timeout = httpx.Timeout(30.0, connect=30.0)
client = httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True)

# Test with HTTP method
async def get_page_with_http(url):
    logger.info(f"Fetching page using HTTP method: {url}")
    try:
        response = await client.get(url)
        if response.status_code == 200:
            logger.info(f"Successfully fetched page, length: {len(response.content)} bytes")
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            logger.info(f"Page title: {title.text if title else 'No title found'}")
            return True
        else:
            logger.error(f"Failed to fetch page: status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error fetching page: {e}")
        return False

# Test with Playwright if available and appropriate
async def get_page_with_playwright(url):
    if is_windows and is_python_312_plus:
        logger.info("Skipping Playwright test on Windows with Python 3.12+")
        return None
        
    try:
        from playwright.async_api import async_playwright
        logger.info(f"Fetching page using Playwright: {url}")
        
        try:
            async with async_playwright() as p:
                try:
                    browser = await p.firefox.launch(headless=True)
                    try:
                        page = await browser.new_page()
                        await page.goto(url, timeout=60000)
                        html_content = await page.content()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        title = soup.find('title')
                        logger.info(f"Page title: {title.text if title else 'No title found'}")
                        return True
                    finally:
                        await browser.close()
                except Exception as e:
                    logger.error(f"Playwright browser error: {e}")
                    return False
        except Exception as e:
            logger.error(f"Playwright initialization error: {e}")
            return False
    except ImportError:
        logger.warning("Playwright not installed")
        return None

async def main():
    test_url = "https://metruyencv.com/"
    
    # Try HTTP method
    http_result = await get_page_with_http(test_url)
    logger.info(f"HTTP method result: {'Success' if http_result else 'Failed'}")
    
    # Try Playwright method if appropriate
    playwright_result = await get_page_with_playwright(test_url)
    if playwright_result is not None:
        logger.info(f"Playwright method result: {'Success' if playwright_result else 'Failed'}")
    else:
        logger.info("Playwright test was skipped")
    
    await client.aclose()

if __name__ == "__main__":
    if is_windows and is_python_312_plus:
        # Set appropriate event loop policy for Windows Python 3.12+
        logger.info("Setting WindowsSelectorEventLoopPolicy for Windows Python 3.12+")
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 