import httpx
from bs4 import BeautifulSoup
from ebooklib import epub
import asyncio
from user_agent import get
from tqdm.asyncio import tqdm
import backoff
from playwright.async_api import async_playwright
import pytesseract
from PIL import Image
import io
from appdirs import *
import configparser
import os.path
import gc
from async_lru import alru_cache
from logger import setup_logger
import time
import sys
import signal
import concurrent.futures

# Initialize logger
logger = setup_logger('mtc_downloader_fast')

# Global variables to track state
is_shutting_down = False
playwright_browsers = []

# Enable garbage collection
gc.enable()
logger.info("Garbage collection enabled")

data_dir = user_config_dir(appname='metruyencv-downloader',appauthor='nguyentd010')
os.makedirs(data_dir, exist_ok=True)
logger.info(f"Using configuration directory: {data_dir}")

if not os.path.isfile(data_dir + '\config.ini'):
    logger.info("Config file not found, creating new file")
    config = configparser.ConfigParser()
    with open(data_dir + '\config.ini', 'w') as configfile:
        config.write(configfile)
    logger.info("Empty config file created")


if os.stat(data_dir+"\config.ini").st_size == 0:
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
    config.read(data_dir + '\config.ini')
    username = str(config.get('data', 'login'))
    password = str(config.get('data', 'password'))
    disk = str(config.get('data', 'disk'))
    max_connections = int(config.get('data', 'max-connection'))
    save = None
    logger.info(f"Loaded config: email={username}, disk={disk}, max_connections={max_connections}")


limits = httpx.Limits(max_keepalive_connections=100, max_connections=max_connections)
timeout = httpx.Timeout(None)
client = httpx.AsyncClient(limits=limits, timeout=timeout)
logger.info(f"Initialized HTTP client with max_connections={max_connections}")

# Base URL for the novel
BASE_URL = 'https://metruyencv.info/truyen/'
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
    with open(data_dir + '\config.ini', 'w') as configfile:
        config.write(configfile)
    logger.info("Configuration saved successfully")

# Signal handler for graceful shutdown
def handle_shutdown_signal(signum, frame):
    global is_shutting_down
    logger.warning(f"Received signal {signum}. Starting graceful shutdown...")
    is_shutting_down = True

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
        l.append(i)
        num += 1
    logger.debug(f"Duplicate removal completed in {time.time() - start_time:.2f} seconds, {len(list) - len(list1)} duplicates removed")
    return list1


async def download_chapter(semaphore, context, title, link, num):
    global is_shutting_down
    
    if is_shutting_down:
        logger.warning(f"Shutdown detected, skipping chapter {num}")
        return None, None, num
        
    logger.debug(f"Downloading chapter {num}: {title}")
    async with semaphore:
        page = await context.new_page()
        await page.goto(link, timeout=0)
        await page.route("**/*", handle_route)
        logger.debug(f"Waiting for content selector for chapter {num}")
        await page.wait_for_selector('xpath=/html/body/div[1]/main/div[4]/div[1]', state='attached', timeout=600000)
        logger.debug(f"Taking screenshot of chapter {num} content")
        image = await page.locator('xpath=/html/body/div[1]/main/div[4]').screenshot()
        await page.close()
        logger.debug(f"Successfully downloaded chapter {num}")
        return title, image, num


async def handle_route(route):
    if "https://googleads" in route.request.url or "https://adclick" in route.request.url:
        logger.debug(f"Blocking ad resource: {route.request.url}")
        await route.abort()
    else:
        await route.continue_()


async def download_missing_chapter(links):
    global is_shutting_down
    
    if is_shutting_down:
        logger.warning("Application is shutting down, skipping download of missing chapters")
        return []
    
    logger.info(f"Downloading {len(links)} missing chapters")
    results = []
    link = links[0][1]
    asyncio_semaphore = asyncio.Semaphore(10)
    logger.debug("Setting up semaphore with 10 concurrent downloads")
    
    async with async_playwright() as p:
        logger.debug("Launching Firefox browser")
        browser = await p.firefox.launch(headless=True)
        # Track browser for cleanup
        playwright_browsers.append(browser)
        
        context = await browser.new_context()
        page = await context.new_page()
        
        logger.info("Logging in to metruyencv.com")
        await page.goto(link)
        await page.locator('xpath=/html/body/div[1]/header/div/div/div[3]/button').click()
        await asyncio.sleep(0.2)
        await page.locator('xpath=/html/body/div[1]/div[2]/div/div[2]/div/div/div/div/div[2]/div[1]/div/div[1]/button').click()
        await asyncio.sleep(0.2)
        logger.debug("Entering login credentials")
        await page.locator('xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[1]/div[2]/input').fill(username)
        await asyncio.sleep(0.2)
        await page.locator('xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[2]/div[2]/input').fill(password)
        await asyncio.sleep(0.2)
        logger.debug("Submitting login form")
        await page.locator('xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[3]/div[1]/button').click()
        await asyncio.sleep(0.2)
        await page.locator('xpath=/html/body/div[1]/div[2]/div/div[2]/div/div/div/div/div[1]/div/div[2]/button').click()
        await asyncio.sleep(0.2)
        
        logger.debug("Setting up reading preferences")
        await page.locator('xpath=/html/body/div[1]/main/div[3]/div[1]/button[1]').click()
        await asyncio.sleep(0.2)
        await page.locator(
            'xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[3]/select').select_option(
            value='Arial')
        await asyncio.sleep(0.2)
        await page.locator(
            'xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[4]/select').select_option(
            value='25px')
        await asyncio.sleep(0.2)
        await page.locator(
            'xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[5]/select').select_option(
            value='150%')
        await asyncio.sleep(0.2)
        await page.close()
        logger.info("Login successful, reading preferences set")
        
        # Check for shutdown signal again
        if is_shutting_down:
            logger.warning("Shutdown detected after login, cancelling download")
            if browser in playwright_browsers:
                playwright_browsers.remove(browser)
            await browser.close()
            return []
        
        logger.info(f"Creating {len(links)} download tasks")
        tasks = [asyncio.create_task(download_chapter(asyncio_semaphore, context, title, link, num)) for title, link, num in links]
        
        try:
            async for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Tải chapters bị thiếu...", unit=" chapters"):
                if is_shutting_down:
                    logger.warning("Shutdown detected while downloading, stopping processing")
                    break
                    
                try:
                    result = await task
                    title = result[0]
                    image = result[1]
                    num = result[2]
                    
                    # Skip if we got an empty result due to shutdown
                    if title is None or image is None:
                        continue
                        
                    logger.debug(f"Processing OCR for chapter {num}")
                    ocr_result = await asyncio.to_thread(ocr, image)
                    missing_html = str(ocr_result).replace('\n\n', '<br/><br/>').replace('\n', ' ')
                    results.append((title, missing_html, num))
                    logger.info(f"Completed processing for chapter {num}, content length: {len(missing_html)}")
                except asyncio.CancelledError:
                    logger.warning("Task was cancelled")
                except Exception as e:
                    logger.error(f"Error processing task: {e}")
        except asyncio.CancelledError:
            logger.warning("Task processing was cancelled")
        finally:
            # Remove from tracked browsers before closing
            if browser in playwright_browsers:
                playwright_browsers.remove(browser)
                
            await context.close()
            await browser.close()
            logger.info(f"Successfully downloaded {len(results)}/{len(links)} missing chapters")
            
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
@backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3, giveup=lambda e: e.response.status_code == 404)
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
        while True:
            # Check for shutdown signal
            if is_shutting_down:
                logger.warning(f"Shutdown detected during download of chapter {chapter_number}")
                return None
                
            logger.debug(f"Sending HTTP request for chapter {chapter_number}")
            resp = await client.get(url, headers=header)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'lxml')
            chapter_content = soup.find('div', class_='break-words')
            chapter_title = str(soup.find('h2', class_='text-center text-gray-600 dark:text-gray-400 text-balance'))
            html = str(chapter_content)
            
            if html.count("<br/>") != 8:
                logger.debug(f"Chapter {chapter_number} content looks valid")
                break
            else:
                i += 1
                logger.warning(f"Chapter {chapter_number} content seems invalid (attempt {i})")
                if i == 15:
                    logger.error(f"Failed to extract chapter {chapter_number} after 15 attempts, adding to missing chapters")
                    missing_chapter.append((chapter_title, url, chapter_number))
                    return None
                    
                # Check for shutdown before retry
                if is_shutting_down:
                    logger.warning(f"Shutdown detected during retry of chapter {chapter_number}")
                    return None
                    
                await asyncio.sleep(1)

        if html is None or chapter_title is None:
            logger.error(f"Không thể tìm thấy chapter {chapter_number}, đang bỏ qua...")
            return None

        logger.info(f"Successfully downloaded chapter {chapter_number}, content length: {len(html)}")
        return chapter_title, html, chapter_number
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"Không thể tìm thấy chapter {chapter_number} (404), đang bỏ qua...")
            return None
        else:
            logger.error(f"HTTP error fetching chapter {chapter_number}: {e}. Đang thử lại...")
            # Check for shutdown before retry with backoff
            if is_shutting_down:
                return None
            await asyncio.sleep(5)
            raise

# Cache the results of the 'get' function for better performance
@alru_cache(maxsize=1024)
async def fetch_chapters(start_chapter, end_chapter, novel_url):
    logger.info(f"Starting download of chapters {start_chapter} to {end_chapter}")
    
    # Giới hạn số lượng tác vụ đồng thời để tránh quá tải
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
    progress_bar = tqdm(total=len(tasks), unit=" chapters", desc="Tải chapters...")
    
    for task in asyncio.as_completed(tasks):
        try:
            if is_shutting_down:
                # Just update progress without waiting
                progress_bar.update(1)
                continue
                
            chapter = await task  # Await here to get the actual result
            progress_bar.update(1)
            if chapter is not None:
                chapters.append(chapter)
        except asyncio.CancelledError:
            logger.warning("Task was cancelled, skipping")
            progress_bar.update(1)
        except Exception as e:
            logger.error(f"Error fetching chapter: {e}")
            progress_bar.update(1)
    
    progress_bar.close()
    
    logger.info(f"Successfully downloaded {len(chapters)}/{end_chapter - start_chapter + 1} chapters")
    
    # Check if we're shutting down before proceeding with missing chapters
    if is_shutting_down:
        logger.warning("Application is shutting down, skipping download of missing chapters")
    elif missing_chapter:
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
    loading_bar = tqdm(total=len(chapters), unit=' chapters', desc='Tạo epub...')
    
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
        loading_bar.update(1)
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


async def main():
    global is_shutting_down, missing_chapter
    
    logger.info("Starting MTC Downloader FAST application")
    start_time = time.time()
    
    try:
        while True:
            missing_chapter = []
            
            # Check if shutdown was requested
            if is_shutting_down:
                logger.warning("Shutdown requested, exiting main loop")
                break
            
            logger.info("Requesting novel information from user")
            novel_url = input('Nhập link metruyencv mà bạn muốn tải: ')
            if '/' == novel_url[-1]:
                logger.debug("Removing trailing slash from URL")
                novel_url = novel_url[:-1]
            start_chapter = int(input('Chapter bắt đầu: '))
            end_chapter = int(input('Chapter kết thúc: '))
            logger.info(f"User provided: URL={novel_url}, start={start_chapter}, end={end_chapter}")

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
                continue

            try:
                logger.info("Downloading cover image")
                image_data = await client.get(image_url, headers=header)
                image_data.raise_for_status()
                image = image_data.content
                logger.debug(f"Cover image downloaded: {len(image)} bytes")
            except httpx.HTTPError as e:
                logger.error(f"Error downloading image: {e}")
                continue

            filename = novel_url.replace(BASE_URL, '').replace('-', '')
            path = f"{disk}:/novel/{title.replace(':', ',').replace('?', '')}"
            
            logger.info(f"Creating output directory: {path}")
            os.makedirs(path, exist_ok=True)

            # Check for shutdown before starting download
            if is_shutting_down:
                logger.warning("Shutdown requested before download, cancelling")
                break

            logger.info("Starting chapter download process")
            chapters = await fetch_chapters(start_chapter, end_chapter, novel_url)
            
            # Check for shutdown before creating EPUB
            if is_shutting_down:
                logger.warning("Shutdown requested before EPUB creation, cancelling")
                break
                
            valid_chapters = [chapter for chapter in chapters if chapter is not None]
            logger.info(f"Downloaded {len(valid_chapters)} valid chapters out of {end_chapter - start_chapter + 1}")

            if valid_chapters:
                logger.info("Creating EPUB file")
                create_epub(title, author, status, attribute, image, valid_chapters, path, filename)
                success_msg = f'Tải thành công {len(valid_chapters)}/{end_chapter - start_chapter + 1} chapter. File của bạn nằm tại "D:/novel"'
                print(success_msg)
                logger.info(success_msg)
            else:
                error_msg = "Lỗi. Tải không thành công"
                print(error_msg)
                logger.error(error_msg)

            continue_download = input("Tải tiếp? (y/n): ").lower() == 'y'
            logger.info(f"User chose to {'continue' if continue_download else 'stop'} downloading")
            
            if not continue_download:
                logger.info("Application terminating as requested by user")
                break
            
            logger.info("Resetting for next download")
            missing_chapter.clear()
            fetch_chapters.cache_clear()
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
        
        # Windows specific event loop policy to avoid task exception errors
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                logger.debug("Set WindowsSelectorEventLoopPolicy for Windows platform")
            except Exception as e:
                logger.warning(f"Could not set Windows event loop policy: {e}")
                
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
