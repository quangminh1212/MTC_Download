import os
import sys
import platform
import logging
import httpx
import asyncio
import time
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

# Default headers
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

async def get_chapter_http_method(url, chapter_number):
    """Use HTTP method to download chapter content without using Playwright"""
    i = 0
    while i < 3:  # Try up to 3 times
        try:
            logger.info(f"Downloading chapter {chapter_number} using HTTP method (attempt {i+1})")
            response = await client.get(url, headers=header)
            if response.status_code == 404:
                logger.error(f"Chapter {chapter_number} not found (404)")
                return None
            
            logger.info(f"Response status: {response.status_code}, Content length: {len(response.content)} bytes")
            
            # Save raw HTML response for inspection
            with open(f"raw_response_{i+1}.html", "wb") as f:
                f.write(response.content)
            logger.info(f"Raw response saved to raw_response_{i+1}.html")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check login status
            login_elements = soup.select('button.bg-primary')
            is_login_page = len(login_elements) > 0 and any('Đăng nhập' in btn.text for btn in login_elements if btn.text)
            if is_login_page:
                logger.warning("Detected login page - authentication may be required")
            
            # Look for chapter title
            chapter_title = soup.find('h2', class_='text-center text-gray-600 dark:text-gray-400 text-balance')
            if not chapter_title:
                logger.info("Primary title selector failed, trying alternative selector")
                chapter_title = soup.find('h2', class_='text-balance')
            
            # Print title if found
            if chapter_title:
                logger.info(f"Found title: {chapter_title.text.strip()}")
            else:
                logger.warning("No chapter title found")
            
            # Look for chapter content
            chapter_content = soup.find('div', id='chapter-content')
            
            # Print content details
            if chapter_content:
                content_text = chapter_content.get_text().strip()
                logger.info(f"Found content div with {len(content_text)} text characters")
                if len(content_text) > 0:
                    logger.info(f"Content preview: {content_text[:100]}...")
            else:
                logger.warning("No chapter content div found")
                
                # Check if we need to log in
                login_required = soup.find(string=lambda text: text and "đăng nhập" in text.lower())
                if login_required:
                    logger.warning("Login appears to be required to access content")
            
            if not chapter_title or not chapter_content:
                logger.warning(f"Couldn't find title or content for chapter {chapter_number} (attempt {i+1})")
                i += 1
                await asyncio.sleep(2)
                continue
                
            chapter_title_str = str(chapter_title)
            chapter_content_str = str(chapter_content)
            
            # Check if content is too short
            if len(chapter_content_str) < 100:
                logger.warning(f"Content for chapter {chapter_number} is too short (attempt {i+1})")
                i += 1
                await asyncio.sleep(2)
                continue
            
            logger.info(f"Successfully downloaded chapter {chapter_number} using HTTP method")
            logger.info(f"Title: {chapter_title.text}")
            logger.info(f"Content length: {len(chapter_content_str)} characters")
            return chapter_title_str, chapter_content_str, chapter_number
            
        except Exception as e:
            logger.error(f"Error downloading chapter {chapter_number} using HTTP method: {e}")
            i += 1
            await asyncio.sleep(5)
    
    # If all attempts fail
    logger.error(f"Failed to download chapter {chapter_number} after multiple attempts")
    return None

async def main():
    novel_url = "https://metruyencv.com/truyen/dai-duong-chi-toi-nguu-vuong-gia"
    chapter_number = 1
    
    url = f'{novel_url}/chuong-{chapter_number}'
    logger.info(f"Testing download of chapter {chapter_number} from URL: {url}")
    
    start_time = time.time()
    result = await get_chapter_http_method(url, chapter_number)
    end_time = time.time()
    
    if result:
        title, content, num = result
        logger.info(f"Successfully downloaded chapter {num}")
        logger.info(f"Title: {BeautifulSoup(title, 'html.parser').text}")
        logger.info(f"Content length: {len(content)} characters")
        logger.info(f"Download completed in {end_time - start_time:.2f} seconds")
        
        # Save content to file for inspection
        with open(f"chapter_{num}.html", "w", encoding="utf-8") as f:
            f.write(f"<html><head><title>Chapter {num}</title></head><body>")
            f.write(f"{title}")
            f.write(f"{content}")
            f.write("</body></html>")
        logger.info(f"Chapter saved to chapter_{num}.html")
    else:
        logger.error("Failed to download chapter")
    
    await client.aclose()

if __name__ == "__main__":
    if is_windows and is_python_312_plus:
        # Set appropriate event loop policy for Windows Python 3.12+
        logger.info("Setting WindowsSelectorEventLoopPolicy for Windows Python 3.12+")
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 