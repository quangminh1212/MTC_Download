import httpx
from bs4 import BeautifulSoup
from ebooklib import epub
import asyncio
from user_agent import get
from tqdm.asyncio import tqdm
import backoff
import os
import subprocess
from playwright.async_api import async_playwright, Error as PlaywrightError
import pytesseract
from PIL import Image
import io
from appdirs import *
import configparser
import os.path
import gc
from async_lru import alru_cache
import sys
import platform
from logger import setup_logger
import time
import signal
import concurrent.futures
import threading
import shutil

# Initialize logger
logger = setup_logger('mtc_downloader')

# Global variables to track state
is_shutting_down = False
playwright_browsers = []

# Check if running on Windows and Python 3.12+ to apply workarounds
is_windows = platform.system() == 'Windows'
is_python_312_plus = sys.version_info >= (3, 12)

if is_windows:
    logger.info("Detected Windows platform")
    if is_python_312_plus:
        logger.info("Detected Python 3.12+, applying special workarounds for asyncio.create_subprocess_exec")
        # Set selector event loop policy for Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Set WindowsSelectorEventLoopPolicy")

# Enable garbage collection
gc.enable()
logger.info("Garbage collection enabled")

data_dir = user_config_dir(appname='metruyencv-downloader',appauthor='nguyentd010')
os.makedirs(data_dir, exist_ok=True)
logger.info(f"Using configuration directory: {data_dir}")

# Sửa các đường dẫn để tránh lỗi invalid escape sequence
config_file = os.path.join(data_dir, 'config.ini')
logger.info(f"Config file path: {config_file}")

# Check for config.txt in current directory first
local_config_file = os.path.join(os.getcwd(), 'config.txt')
if os.path.isfile(local_config_file):
    logger.info(f"Found local config file: {local_config_file}")
    try:
        # Read from config.txt with multiple encodings
        config_data = {}
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'utf-16']
        
        for encoding in encodings_to_try:
            try:
                logger.debug(f"Trying to read config.txt with encoding: {encoding}")
                with open(local_config_file, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config_data[key.strip()] = value.strip()
                # If we got here, the encoding worked
                logger.info(f"Successfully read config.txt using {encoding} encoding")
                break
            except UnicodeDecodeError:
                logger.debug(f"Failed to read config.txt with encoding {encoding}")
                continue
            except Exception as e:
                logger.error(f"Error reading config.txt with encoding {encoding}: {e}")
                continue
        
        if not config_data:
            logger.error("Could not read config.txt with any encoding, falling back to defaults")
            raise ValueError("Failed to read config file with any encoding")
        
        username = config_data.get('email', '')
        password = config_data.get('password', '')
        disk = config_data.get('disk', 'C')
        max_connections = int(config_data.get('max_connections', '50'))
        
        # Check for command-line arguments for novel URL and chapters
        if len(sys.argv) > 3:
            novel_url = sys.argv[1]
            start_chapter = int(sys.argv[2])
            end_chapter = int(sys.argv[3])
            logger.info(f"Using command line parameters for novel info")
        else:
            novel_url = config_data.get('novel_url', '')
            start_chapter = int(config_data.get('start_chapter', '1'))
            end_chapter = int(config_data.get('end_chapter', '10'))
            logger.info(f"Using config file parameters for novel info")
            
        logger.info(f"Loaded config from local file: email={username}, disk={disk}, max_connections={max_connections}")
        logger.info(f"Novel URL: {novel_url}, Chapters: {start_chapter} to {end_chapter}")
        
        save = None
        # Make sure the variables are accessible outside this block
        globals()['username'] = username
        globals()['password'] = password
        globals()['disk'] = disk
        globals()['max_connections'] = max_connections
        globals()['novel_url'] = novel_url
        globals()['start_chapter'] = start_chapter
        globals()['end_chapter'] = end_chapter
        
    except Exception as e:
        logger.error(f"Error reading local config: {e}")
        if not os.path.isfile(config_file):
            logger.info("Config file not found, creating new file")
            config = configparser.ConfigParser()
            with open(config_file, 'w') as configfile:
                config.write(configfile)
            logger.info("Empty config file created")
        
        missing_chapter = []
        logger.info("Config file is empty, requesting user input")
        username = str(input('Email tài khoản metruyencv?:'))
        password = str(input('Password?:'))
        disk = str(input('Ổ đĩa lưu truyện(C/D):')).capitalize()
        max_connections = int(input('''Max Connections (10 -> 1000) 
        Note: Càng cao thì rủi ro lỗi cũng tăng, chỉ số tối ưu nhất là 50 : '''))
        save = str(input('Lưu config?(Y/N):')).capitalize()
        logger.info(f"User provided config: email={username}, disk={disk}, max_connections={max_connections}, save={save}")
        
        # Need to ask for novel info since config file read failed
        novel_url = input('Nhập link metruyencv mà bạn muốn tải: ')
        start_chapter = int(input('Chapter bắt đầu: '))
        end_chapter = int(input('Chapter kết thúc: '))
        logger.info(f"User provided novel info: URL={novel_url}, start={start_chapter}, end={end_chapter}")
else:
    if not os.path.isfile(config_file):
        logger.info("Config file not found, creating new file")
        config = configparser.ConfigParser()
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        logger.info("Empty config file created")
    
    missing_chapter = []
    if os.stat(config_file).st_size == 0:
        logger.info("Config file is empty, requesting user input")
        username = str(input('Email tài khoản metruyencv?:'))
        password = str(input('Password?:'))
        disk = str(input('Ổ đĩa lưu truyện(C/D):')).capitalize()
        max_connections = int(input('''Max Connections (10 -> 1000) 
        Note: Càng cao thì rủi ro lỗi cũng tăng, chỉ số tối ưu nhất là 50 : '''))
        save = str(input('Lưu config?(Y/N):')).capitalize()
        logger.info(f"User provided config: email={username}, disk={disk}, max_connections={max_connections}, save={save}")
    
    else:
        logger.info("Reading configuration from file")
        config = configparser.ConfigParser()
        config.read(config_file)
        username = str(config.get('data', 'login'))
        password = str(config.get('data', 'password'))
        disk = str(config.get('data', 'disk'))
        max_connections = int(config.get('data', 'max-connection'))
        save = None
        logger.info(f"Loaded config: email={username}, disk={disk}, max_connections={max_connections}")

limits = httpx.Limits(max_keepalive_connections=100, max_connections=max_connections)
timeout = httpx.Timeout(None)
# Cấu hình httpx client để follow redirects
client = httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True)
logger.info(f"Initialized HTTP client with max_connections={max_connections}")

# Base URL for the novel - đổi thành .com vì đây là domain chính thức hiện nay
BASE_URL = 'https://metruyencv.com/truyen/'
logger.info(f"Using base URL: {BASE_URL}")

user_agent = get()
logger.debug(f"Generated user agent: {user_agent}")

file_location = os.getcwd()
logger.debug(f"Current working directory: {file_location}")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
logger.info("Tesseract OCR path set")

header = {'user-agent': user_agent}
logger.debug("HTTP headers configured")

if save == 'Y':
    logger.info("Saving configuration to file")
    config = configparser.ConfigParser()
    config['data'] = {'login': username, 'password': password, 'disk' : disk, 'max-connection' : max_connections}

    # Write the configuration to a file
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    logger.info("Configuration saved successfully")

# Use synchronous playwright browser launching to work around asyncio.create_subprocess_exec issues
def launch_browser_sync(browser_type, headless=True):
    """Launch browser synchronously using subprocess instead of asyncio"""
    logger.info(f"Launching browser in synchronous mode: {browser_type}")
    if is_windows and is_python_312_plus:
        try:
            # Find the playwright executable
            import playwright
            playwright_path = os.path.dirname(playwright.__file__)
            driver_executable = os.path.join(playwright_path, "..", "..", "..", "bin", "playwright.cmd")
            if not os.path.exists(driver_executable):
                driver_executable = shutil.which("playwright") or "playwright"
                
            # Launch the browser driver using subprocess
            logger.debug(f"Using playwright executable: {driver_executable}")
            subprocess.run([driver_executable, "install", browser_type], 
                           check=False, capture_output=True)
            
            return True
        except Exception as e:
            logger.error(f"Error launching browser synchronously: {e}")
            return False
    return None

# Launch browsers synchronously on Windows Python 3.12+
if is_windows and is_python_312_plus:
    logger.info("Pre-installing Firefox browser for Playwright")
    launch_browser_sync("firefox")

def ocr(image: bytes) -> str:
    logger.debug("Starting OCR processing")
    start_time = time.time()
    image = Image.open(io.BytesIO(image))
    image = image.convert('L')
    text = pytesseract.image_to_string(image, lang='vie')
    logger.debug(f"OCR completed in {time.time() - start_time:.2f} seconds")
    return text

def delete_dupe(list):
    logger.debug(f"Removing duplicates from list with {len(list)} items")
    start_time = time.time()
    list1 = list.copy()
    l = []
    num = 0
    for i, j, k in list1:
        if k in l:
            del list1[num]
        l.append(k)
        num += 1
    logger.debug(f"Duplicate removal completed in {time.time() - start_time:.2f} seconds, {len(list) - len(list1)} duplicates removed")
    return list1

# Signal handler for graceful shutdown
def handle_shutdown_signal(signum, frame):
    global is_shutting_down
    logger.warning(f"Received signal {signum}. Starting graceful shutdown...")
    is_shutting_down = True
    # Close all tasks - we'll handle this in the main function

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

async def close_all_browsers():
    """Close all playwright browsers gracefully"""
    logger.info(f"Closing {len(playwright_browsers)} browser instances...")
    close_tasks = []
    for browser in playwright_browsers:
        if browser and not browser.is_closed():
            try:
                close_tasks.append(asyncio.create_task(browser.close()))
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
    
    if close_tasks:
        await asyncio.gather(*close_tasks, return_exceptions=True)
    logger.info("All browsers closed")

async def download_missing_chapter(links):
    logger.info(f"Downloading {len(links)} missing chapters")
    results = []
    setting = True
    
    if is_shutting_down:
        logger.warning("Application is shutting down, skipping download of missing chapters")
        return results
        
    try:
        # Use a fallback approach for browser launching on Windows Python 3.12+
        if is_windows and is_python_312_plus:
            import subprocess
            import tempfile
            import json
            from playwright._impl._api_types import Error
            
            logger.info("Using fallback approach for browser launching on Windows Python 3.12+")
            
            # Use an existing Firefox installation if available
            # This avoids the need for asyncio.create_subprocess_exec
            firefox_paths = [
                os.path.expandvars("%ProgramFiles%\\Mozilla Firefox\\firefox.exe"),
                os.path.expandvars("%ProgramFiles(x86)%\\Mozilla Firefox\\firefox.exe")
            ]
            
            firefox_path = None
            for path in firefox_paths:
                if os.path.exists(path):
                    firefox_path = path
                    break
                    
            if firefox_path:
                logger.info(f"Found Firefox installation at {firefox_path}")
            else:
                logger.warning("No Firefox installation found. Will attempt to use Playwright's bundled browsers.")
    
    except Exception as e:
        logger.error(f"Error setting up browser environment: {e}")
    
    try:
        async with async_playwright() as p:
            try:
                logger.debug("Launching Firefox browser")
                # Add executable_path if we found a Firefox installation
                browser_args = []
                browser = await p.firefox.launch(headless=True, args=browser_args)
                # Track browser for cleanup
                playwright_browsers.append(browser)
                
                page = await browser.new_page()
                
                # Đăng nhập trước
                logger.info("Logging in to metruyencv.com")
                await page.goto('https://metruyencv.com/',timeout=0)
                logger.debug("Navigating to login page")
                await page.locator('xpath=/html/body/div[1]/header/div/div/div[3]/button').click()
                await asyncio.sleep(1)
                await page.locator('xpath=/html/body/div[1]/div[2]/div/div[2]/div/div/div/div/div[2]/div[1]/div/div[1]/button').click()
                await asyncio.sleep(1)
                logger.debug("Entering login credentials")
                await page.locator('xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[1]/div[2]/input').fill(username)
                await asyncio.sleep(1)
                await page.locator('xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[2]/div[2]/input').fill(password)
                await asyncio.sleep(1)
                logger.debug("Submitting login form")
                await page.locator('xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[3]/div[1]/button').click()
                await asyncio.sleep(1)
                await page.locator('xpath=/html/body/div[1]/div[2]/div/div[2]/div/div/div/div/div[1]/div/div[2]/button').click()
                await asyncio.sleep(1)
                logger.info("Login successful")
                
                for title, link, num in links:
                    # Check for shutdown signal
                    if is_shutting_down:
                        logger.warning(f"Shutdown requested, stopping at chapter {num}")
                        break
                        
                    try:
                        logger.info(f"Downloading missing chapter {num}: {title}")
                        await page.goto(link, timeout=60000)
                        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] and "chapter-content" not in route.request.url else route.continue_())
                        
                        # Nếu cần thiết lập cấu hình đọc
                        if setting:
                            try:
                                logger.debug("Setting up reading preferences")
                                await page.locator('xpath=/html/body/div[1]/main/div[3]/div[1]/button[1]').click()
                                await page.locator('xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[3]/select').select_option(value ='Times New Roman')
                                await page.locator('xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[4]/select').select_option(value='50px')
                                await page.reload()
                                setting = False
                                logger.debug("Reading preferences set")
                            except Exception as e:
                                logger.error(f"Không thể thiết lập cấu hình đọc: {e}")
                                setting = False  # Vẫn tiếp tục mặc dù không thiết lập được
                        
                        # Chờ nội dung chương tải xong
                        logger.debug("Waiting for chapter content to load")
                        await page.wait_for_selector("#chapter-content", state="attached", timeout=30000)
                        
                        # Lấy HTML của trang
                        html_content = await page.content()
                        soup = BeautifulSoup(html_content, 'lxml')
                        
                        # Lấy nội dung chương
                        chapter_content = soup.find('div', id='chapter-content')
                        
                        if chapter_content:
                            chapter_content_str = str(chapter_content)
                            
                            # Kiểm tra nếu nội dung quá ngắn
                            if len(chapter_content_str) < 100:
                                logger.warning(f"Nội dung chương {num} quá ngắn, có thể không tải được đầy đủ")
                                continue
                            
                            results.append((title, chapter_content_str, num))
                            logger.info(f'Đã tải xong chap {num}, độ dài: {len(chapter_content_str)} ký tự')
                        else:
                            logger.error(f"Không thể tìm thấy nội dung chương {num}")
                    except Exception as e:
                        logger.error(f"Lỗi khi tải chương {num}: {e}")
                
                # Remove from tracked browsers before closing
                if browser in playwright_browsers:
                    playwright_browsers.remove(browser)
                    
                await browser.close()
                logger.info(f"Successfully downloaded {len(results)}/{len(links)} missing chapters")
            except PlaywrightError as pe:
                logger.error(f"Playwright error: {pe}")
                return results
            except Exception as e:
                logger.error(f"Error in browser session: {e}")
                return results
    except Exception as e:
        logger.error(f"Failed to initialize Playwright: {e}")
        
    return results

def sort_chapters(list_of_chapters):
    logger.debug(f"Sorting {len(list_of_chapters)} chapters")
    start_time = time.time()
    lst = len(list_of_chapters)
    for i in range(0, lst):
        for j in range(0, lst - i - 1):
            if (list_of_chapters[j][2] > list_of_chapters[j + 1][2]):
                temp = list_of_chapters[j]
                list_of_chapters[j] = list_of_chapters[j + 1]
                list_of_chapters[j + 1] = temp
    logger.debug(f"Chapter sorting completed in {time.time() - start_time:.2f} seconds")
    return list_of_chapters

# Retry decorator for handling transient errors, excluding 404 errors
@backoff.on_exception(backoff.expo, Exception, max_tries=3, giveup=lambda e: str(e) == "404")
async def get_chapter_with_retry(chapter_number, novel_url):
    global is_shutting_down
    
    # Check if we're shutting down before starting
    if is_shutting_down:
        logger.warning(f"Shutdown in progress, skipping chapter {chapter_number}")
        return None
        
    url = f'{novel_url}/chuong-{chapter_number}'
    i = 0
    try:
        logger.info(f"Attempting to download chapter {chapter_number}")
        # Sử dụng Playwright để tải nội dung chương
        try:
            async with async_playwright() as p:
                try:
                    logger.debug(f"Launching browser for chapter {chapter_number}")
                    browser = await p.firefox.launch(headless=True)
                    # Track browser for cleanup
                    playwright_browsers.append(browser)
                    
                    try:
                        # Check again if we're shutting down
                        if is_shutting_down:
                            logger.warning(f"Shutdown detected while loading chapter {chapter_number}, aborting")
                            return None
                            
                        page = await browser.new_page()
                        
                        # Chặn quảng cáo và một số tài nguyên không cần thiết để tăng tốc độ tải
                        logger.debug("Configuring resource blocking to improve load speed")
                        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] and "chapter-content" not in route.request.url else route.continue_())
                        
                        logger.debug(f"Navigating to URL: {url}")
                        await page.goto(url, timeout=60000)  # Tăng timeout lên 60 giây
                        
                        # Chờ đến khi nội dung chương được tải
                        logger.debug("Waiting for chapter content to load")
                        await page.wait_for_selector("#chapter-content", state="attached", timeout=30000)
                        
                        # Lấy HTML của trang
                        logger.debug("Extracting HTML content")
                        html_content = await page.content()
                        soup = BeautifulSoup(html_content, 'lxml')
                        
                        # Lấy tiêu đề chương
                        chapter_title = soup.find('h2', class_='text-center text-gray-600 dark:text-gray-400 text-balance')
                        if not chapter_title:
                            logger.debug("Primary title selector failed, trying alternative selector")
                            chapter_title = soup.find('h2', class_='text-balance')
                        
                        # Lấy nội dung chương
                        chapter_content = soup.find('div', id='chapter-content')
                        
                        if not chapter_title or not chapter_content:
                            logger.warning(f"Không thể tìm thấy tiêu đề hoặc nội dung của chương {chapter_number}")
                            if i == 10:
                                logger.error(f"Failed to extract chapter {chapter_number} after 10 attempts, adding to missing chapters")
                                missing_chapter.append((str(chapter_title), url, chapter_number))
                                return None
                            i += 1
                            logger.debug(f"Retrying chapter {chapter_number}, attempt {i}")
                            await asyncio.sleep(2)
                            return await get_chapter_with_retry(chapter_number, novel_url)
                        
                        # Chuyển đổi sang chuỗi
                        chapter_title_str = str(chapter_title)
                        chapter_content_str = str(chapter_content)
                        
                        # Kiểm tra nếu nội dung quá ngắn
                        if len(chapter_content_str) < 100:
                            logger.warning(f"Nội dung chương {chapter_number} quá ngắn, có thể không tải được đầy đủ")
                            if i == 5:
                                logger.error(f"Content too short for chapter {chapter_number} after 5 attempts, adding to missing chapters")
                                missing_chapter.append((chapter_title_str, url, chapter_number))
                                return None
                            i += 1
                            logger.debug(f"Retrying chapter {chapter_number}, attempt {i}")
                            await asyncio.sleep(2)
                            return await get_chapter_with_retry(chapter_number, novel_url)
                        
                        logger.info(f"Đã tải xong chương {chapter_number}, độ dài: {len(chapter_content_str)} ký tự")
                        return chapter_title_str, chapter_content_str, chapter_number
                    finally:
                        logger.debug(f"Closing browser for chapter {chapter_number}")
                        # Remove from tracked browsers before closing
                        if browser in playwright_browsers:
                            playwright_browsers.remove(browser)
                        await browser.close()
                except PlaywrightError as pe:
                    logger.error(f"Playwright error while loading chapter {chapter_number}: {pe}")
                    raise Exception(f"Playwright error: {pe}")
        except Exception as e:
            if "NotImplementedError" in str(e):
                logger.error(f"NotImplementedError while loading chapter {chapter_number}, this is likely due to Windows Python 3.12 asyncio limitations")
                # Try a fallback approach using httpx directly
                try:
                    logger.info(f"Attempting fallback HTTP method for chapter {chapter_number}")
                    response = await client.get(url, headers=header)
                    if response.status_code == 404:
                        logger.error(f"Chapter {chapter_number} not found (404)")
                        return None
                    
                    soup = BeautifulSoup(response.content, 'lxml')
                    chapter_title = soup.find('h2', class_='text-center text-gray-600 dark:text-gray-400 text-balance')
                    if not chapter_title:
                        chapter_title = soup.find('h2', class_='text-balance')
                    
                    chapter_content = soup.find('div', id='chapter-content')
                    
                    if chapter_title and chapter_content and len(str(chapter_content)) > 100:
                        return str(chapter_title), str(chapter_content), chapter_number
                    else:
                        logger.error(f"Failed to extract content using fallback method for chapter {chapter_number}")
                        missing_chapter.append((str(chapter_title) if chapter_title else "Unknown", url, chapter_number))
                        return None
                except Exception as http_err:
                    logger.error(f"Fallback method also failed for chapter {chapter_number}: {http_err}")
                    raise
            else:
                raise
                
    except Exception as e:
        if str(e) == "404" or "status=404" in str(e):
            logger.error(f"\nLỗi: Không thể tìm thấy chapter {chapter_number} (404), đang bỏ qua...")
            return None
        else:
            logger.error(f"Lỗi khi tải chapter {chapter_number}: {e}. Đang thử lại...")
            await asyncio.sleep(5)
            raise

# Cache the results of the 'get' function for better performance
@alru_cache(maxsize=1024)
async def fetch_chapters(start_chapter, end_chapter, novel_url):
    logger.info(f"Starting download of chapters {start_chapter} to {end_chapter}")
    
    # Giới hạn số lượng tác vụ đồng thời
    max_concurrent_tasks = 5
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    logger.info(f"Using semaphore to limit concurrent tasks to {max_concurrent_tasks}")
    
    chapters = []
    tasks = []
    
    # Create tasks with semaphore control
    async def bounded_get_chapter(chapter_number, novel_url):
        async with semaphore:
            if is_shutting_down:
                return None
            return await get_chapter_with_retry(chapter_number, novel_url)
    
    for number in range(start_chapter, end_chapter + 1):
        if is_shutting_down:
            logger.warning("Shutdown in progress, stopping task creation")
            break
        tasks.append(asyncio.create_task(bounded_get_chapter(number, novel_url)))
    
    # Use tqdm to display a progress bar
    progress_bar = tqdm(total=end_chapter - start_chapter + 1, desc="Tải chapters...", unit=" chapters")
    
    # Safely process completed tasks
    completed_tasks = 0
    for task in tasks:
        if is_shutting_down:
            # Cancel remaining tasks
            if not task.done():
                task.cancel()
            continue
            
        try:
            chapter = await task
            if chapter is not None:
                chapters.append(chapter)
        except asyncio.CancelledError:
            logger.warning("Task was cancelled, skipping")
        except Exception as e:
            logger.error(f"Error fetching chapter: {e}")
        finally:
            completed_tasks += 1
            progress_bar.update(1)
    
    progress_bar.close()
    
    logger.info(f"Successfully downloaded {len(chapters)}/{end_chapter - start_chapter + 1} chapters")
    
    # Check if we're shutting down before proceeding with missing chapters
    if is_shutting_down:
        logger.warning("Application is shutting down, skipping download of missing chapters")
    elif missing_chapter:
        logger.info('Đang tải chapters bị thiếu...')
        logger.info(f"Attempting to download {len(missing_chapter)} missing chapters")
        missing_downloaded = await download_missing_chapter(missing_chapter)
        chapters += missing_downloaded
        logger.info(f"Downloaded {len(missing_downloaded)}/{len(missing_chapter)} missing chapters")
    
    logger.debug("Removing duplicates")
    chapters = delete_dupe(chapters)
    logger.debug("Sorting chapters")
    sorted_chapters = sort_chapters(chapters)
    logger.info(f"Processed a total of {len(sorted_chapters)} valid chapters")
    return sorted_chapters

def create_epub(title, author, status, attribute, image, chapters, path, filename):
    logger.info(f"Creating EPUB for '{title}' with {len(chapters)} chapters")
    logger.debug(f"Author: {author}, Status: {status}, Output path: {path}")
    
    book = epub.EpubBook()
    book.set_title(title)
    book.set_identifier("nguyentd010")
    book.add_author(author)
    book.set_language('vn')
    book.add_metadata(None, 'meta', '', {'name': 'status', 'content': status})
    book.add_metadata(None, 'meta', '', {'name': 'chapter', 'content': str(len(chapters))})
    book.set_cover(content=image, file_name='cover.jpg')
    book.add_metadata(None, 'meta', '', {'name': 'attribute', 'content': attribute})
    
    logger.debug("EPUB metadata set")
    p = 1
    chapter_num = []
    
    logger.debug("Processing chapters for EPUB")
    for chapter_title, chapter, i in chapters:
        chapter_num.append(i)
        chapter_title = BeautifulSoup(chapter_title, 'lxml').text
        chapter = f'<h2>{chapter_title}</h2>' + "<h3>Generated by nguyentd010's metruyencv_downloader</h3>" + chapter
        if p == 1:
            chapter = f"<h1>{title}</h1>" + chapter
        p += 1
        html = BeautifulSoup(chapter, 'lxml')
        file_name = f'chapter{i}-{chapter_title}.html'
        chapter = epub.EpubHtml(lang='vn', title=chapter_title, file_name=file_name, uid=f'chapter{i}')
        chapter.content = str(html)
        book.add_item(chapter)
        logger.debug(f"Added chapter {i} to EPUB")

    style = '''
        body {
            font-family: Cambria, Liberation Serif, Bitstream Vera Serif, Georgia, Times, Times New Roman, serif;
        }
        h1 {
             text-align: left;
             text-transform: uppercase;
             font-weight: 400;     
        }
        h2 {
             text-align: left;
             text-transform: uppercase;
             font-weight: 300;     
        }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    logger.debug("Added CSS styling to EPUB")

    book.spine = [f'chapter{i}' for i in chapter_num]
    
    output_path = f'{path}/{filename}.epub'
    logger.info(f"Writing EPUB file to {output_path}")
    epub.write_epub(output_path, book)
    logger.info(f"EPUB file successfully created: {output_path}")

def read_config_file(file_path):
    """Đọc file cấu hình với các mã hóa khác nhau để tránh lỗi"""
    logger.debug(f"Reading config file: {file_path}")
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            logger.debug(f"Trying encoding: {encoding}")
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                logger.debug(f"Successfully read file with encoding: {encoding}")
                return content
        except UnicodeDecodeError:
            logger.debug(f"Failed to decode with encoding: {encoding}")
            continue
    
    # Nếu tất cả các mã hóa đều thất bại, đọc dưới dạng nhị phân và bỏ qua BOM
    logger.warning("All standard encodings failed, trying binary read with BOM handling")
    with open(file_path, 'rb') as f:
        content = f.read()
        # Bỏ qua BOM nếu có
        if content.startswith(b'\xef\xbb\xbf'):
            logger.debug("Detected UTF-8 BOM, removing")
            content = content[3:]
        # Bỏ qua BOM UTF-16
        elif content.startswith(b'\xff\xfe') or content.startswith(b'\xfe\xff'):
            logger.debug("Detected UTF-16 BOM, removing")
            content = content[2:]
        decoded = content.decode('utf-8', errors='ignore')
        logger.debug("Successfully decoded file with binary mode and BOM handling")
        return decoded

async def main():
    global is_shutting_down
    
    logger.info("Starting MTC Downloader application")
    start_time = time.time()
    
    try:
        # Check for AUTOMATED_RUN environment variable
        automated_run = os.environ.get('AUTOMATED_RUN', '0') == '1'
        if automated_run:
            logger.info("Running in automated mode from batch file")
            novel_url = os.environ.get('NOVEL_URL', '')
            start_chapter_str = os.environ.get('START_CHAPTER', '1')
            end_chapter_str = os.environ.get('END_CHAPTER', '10')
            
            try:
                start_chapter = int(start_chapter_str)
                end_chapter = int(end_chapter_str)
                logger.info(f"Using environment variables: URL={novel_url}, start={start_chapter}, end={end_chapter}")
                # Export to globals for rest of application
                globals()['novel_url'] = novel_url
                globals()['start_chapter'] = start_chapter
                globals()['end_chapter'] = end_chapter
            except ValueError as e:
                logger.error(f"Error parsing environment variables: {e}")
        
        # Lấy thông tin từ tham số dòng lệnh hoặc config.txt
        try:
            # Set default values for novel_url, start_chapter and end_chapter
            # These should have been set in the config loading section at the beginning
            # If not, let's handle it gracefully here
            if 'novel_url' not in globals():
                logger.info("Novel URL not set in global variables")
                # Check if we have command line parameters
                if len(sys.argv) > 3:
                    novel_url = sys.argv[1]
                    start_chapter = int(sys.argv[2])
                    end_chapter = int(sys.argv[3])
                    logger.info(f"Using command line parameters")
                else:
                    # Fallback to prompting user if needed
                    logger.info("Insufficient parameters, requesting user input")
                    novel_url = input('Nhập link metruyencv mà bạn muốn tải: ')
                    start_chapter = int(input('Chapter bắt đầu: '))
                    end_chapter = int(input('Chapter kết thúc: '))
            
            logger.info(f"URL: {novel_url}")
            logger.info(f"Chương bắt đầu: {start_chapter}")
            logger.info(f"Chương kết thúc: {end_chapter}")
        except Exception as e:
            logger.error(f"Error reading parameters: {e}")
            novel_url = input('Nhập link metruyencv mà bạn muốn tải: ')
            start_chapter = int(input('Chapter bắt đầu: '))
            end_chapter = int(input('Chapter kết thúc: '))
            logger.info(f"User provided after error: URL={novel_url}, start={start_chapter}, end={end_chapter}")
        
        # Đảm bảo URL kết thúc đúng
        if '/' == novel_url[-1]:
            logger.debug("Removing trailing slash from URL")
            novel_url = novel_url[:-1]
        
        # Thay thế .info bằng .com vì trang web chính thức hiện nay là .com
        if 'metruyencv.info' in novel_url:
            logger.info(f"Converting URL from .info to .com domain")
            novel_url = novel_url.replace('metruyencv.info', 'metruyencv.com')
            logger.info(f"Updated URL: {novel_url}")
        
        # In ra các giá trị đọc được
        print(f"URL: {novel_url}")
        print(f"Chương bắt đầu: {start_chapter}")
        print(f"Chương kết thúc: {end_chapter}")

        try:
            logger.info("Fetching novel information")
            response = await client.get(novel_url, headers=header)
            response.raise_for_status()
            logger.debug(f"Novel page fetched successfully: {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'lxml')
            title = str(soup.find('h1', class_='mb-2').text)
            author = str(soup.find('a', class_='text-gray-500').text).strip()
            status = str(
                soup.find('a', class_='inline-flex border border-primary rounded px-2 py-1 text-primary').select_one(
                    'span').text).strip()
            attribute = str(soup.find('a',
                                    class_='inline-flex border border-rose-700 dark:border-red-400 rounded px-2 py-1 text-rose-700 dark:text-red-400').text)
            image_url = soup.find('img', class_='w-44 h-60 shadow-lg rounded mx-auto')['src']
            
            logger.info(f"Novel info: Title='{title}', Author='{author}', Status='{status}'")
            logger.debug(f"Cover image URL: {image_url}")
        except (httpx.HTTPError, TypeError, KeyError) as e:
            logger.error(f"Error fetching novel information: {e}")
            return

        try:
            logger.info("Downloading cover image")
            image_data = await client.get(image_url, headers=header)
            image_data.raise_for_status()
            image = image_data.content
            logger.debug(f"Cover image downloaded: {len(image)} bytes")
        except httpx.HTTPError as e:
            logger.error(f"Error downloading image: {e}")
            return

        filename = novel_url.replace(BASE_URL, '').replace('-', '')
        path = f"{disk}:/novel/{title.replace(':', ',').replace('?', '')}"
        
        logger.info(f"Creating output directory: {path}")
        os.makedirs(path, exist_ok=True)

        logger.info("Starting chapter download process")
        
        # Check if shutdown is requested
        if is_shutting_down:
            logger.warning("Shutdown requested, cancelling download")
            return
            
        chapters = await fetch_chapters(start_chapter, end_chapter, novel_url)
        
        # Check again if shutdown is requested
        if is_shutting_down:
            logger.warning("Shutdown requested, cancelling EPUB creation")
            return
            
        valid_chapters = [chapter for chapter in chapters if chapter is not None]
        logger.info(f"Downloaded {len(valid_chapters)} valid chapters out of {end_chapter - start_chapter + 1}")

        if valid_chapters:
            logger.info("Creating EPUB file")
            create_epub(title, author, status, attribute, image, valid_chapters, path, filename)
            success_msg = f'Tải thành công {len(valid_chapters)}/{end_chapter - start_chapter + 1} chapter. File của bạn nằm tại "{disk}:/novel"'
            print(success_msg)
            logger.info(success_msg)
        else:
            error_msg = "Lỗi. Tải không thành công"
            print(error_msg)
            logger.error(error_msg)

        # Automatically continue without asking if the program should be run from run.bat with config
        if 'AUTOMATED_RUN' not in os.environ:
            continue_download = input("Tải tiếp? (y/n): ").lower() == 'y'
            logger.info(f"User chose to {'continue' if continue_download else 'stop'} downloading")
            
            if continue_download:
                return await main()  # Recursively call main to continue downloading
        else:
            logger.info("Automated run completed, exiting without prompt")
            
        total_time = time.time() - start_time
        logger.info(f"Download session completed in {total_time:.2f} seconds")
            
    finally:
        # Ensure proper cleanup
        await close_all_browsers()
        await client.aclose()
        logger.info("HTTP client closed")

async def run_with_graceful_shutdown():
    """Wrapper to handle graceful shutdown"""
    try:
        await main()
    except asyncio.CancelledError:
        logger.warning("Main task was cancelled")
    finally:
        logger.info("Performing final cleanup")
        await close_all_browsers()
        
        # Close the httpx client if it exists
        try:
            await client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")

if __name__ == '__main__':
    try:
        logger.info("Application started")
        
        # Fix command line argument parsing
        # The issue is that sys.argv[0] is the script name, not the first argument
        if len(sys.argv) > 3:
            logger.info("Processing command line arguments")
            try:
                # Arguments are properly positioned starting from index 1
                novel_url = sys.argv[1]
                start_chapter = int(sys.argv[2])
                end_chapter = int(sys.argv[3])
                logger.info(f"Command line arguments parsed: URL={novel_url}, start={start_chapter}, end={end_chapter}")
            except ValueError as e:
                logger.error(f"Error parsing command line arguments: {e}")
                logger.info("Will fall back to config file or user input")
        
        # Run with improved exception handling
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_with_graceful_shutdown())
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt received, initiating graceful shutdown")
            is_shutting_down = True
            
            # Cancel all tasks
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                if not task.done() and task != asyncio.current_task():
                    task.cancel()
                    
            # Run the event loop until all tasks are cancelled
            try:
                logger.info("Waiting for tasks to cancel...")
                loop.run_until_complete(close_all_browsers())
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            except asyncio.CancelledError:
                pass
                
        finally:
            # Clean shutdown
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            
        logger.info("Application completed successfully")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"Critical error: {e}")
        sys.exit(1)
