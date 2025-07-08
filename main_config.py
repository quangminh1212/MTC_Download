# -*- coding: utf-8 -*-
"""
MeTruyenCV Downloader with Configuration Management
Version with config.txt support
"""

import sys
import os

# Set encoding for Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

import httpx
from bs4 import BeautifulSoup
from ebooklib import epub
import asyncio
from user_agent import get
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib")
from tqdm.asyncio import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pytesseract
from PIL import Image
import io
import gc
from async_lru import alru_cache
import time
import base64
from config_manager import ConfigManager

# Enable garbage collection
gc.enable()

# Initialize config manager
config = ConfigManager()

# Get configuration
login_info = config.get_login_info()
download_settings = config.get_download_settings()
app_settings = config.get_app_settings()

username = login_info['email']
password = login_info['password']
disk = download_settings['drive']
max_connections = download_settings['max_connections']

missing_chapter = []

# Setup HTTP client
limits = httpx.Limits(max_keepalive_connections=100, max_connections=max_connections)
timeout = httpx.Timeout(None)
client = httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True)

# Base URLs
BASE_URLS = [
    'https://metruyencv.biz/truyen/',
    'https://metruyencv.com/truyen/',
    'https://metruyencv.info/truyen/'
]

user_agent = get() if not app_settings['user_agent'] else app_settings['user_agent']
file_location = os.getcwd()
pytesseract.pytesseract.tesseract_cmd = fr'{file_location}\Tesseract-OCR\tesseract.exe'
header = {'user-agent': user_agent}

def ocr(image_data: bytes) -> str:
    """OCR function for canvas elements"""
    if not app_settings['use_ocr']:
        return ""
    
    try:
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('L')
        text = pytesseract.image_to_string(image, lang='vie')
        return text
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def delete_dupe(list):
    """Remove duplicate chapters"""
    list1 = list.copy()
    l = []
    num = 0
    for i, j, k in list1:
        if k in l:
            del list1[num]
        l.append(k)
        num += 1
    return list1

def get_selenium_driver():
    """Create and configure Selenium driver with robust error handling"""

    # Try Firefox first
    try:
        options = Options()
        if app_settings['headless']:
            options.add_argument('--headless')

        # Basic options only to avoid compatibility issues
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Firefox preferences
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference('useAutomationExtension', False)
        options.set_preference("general.useragent.override", user_agent)

        # Set page load strategy to eager for faster loading
        options.page_load_strategy = 'eager'

        driver = webdriver.Firefox(options=options)

        # Set conservative timeouts
        driver.implicitly_wait(5)
        driver.set_page_load_timeout(20)

        print("🦊 Sử dụng Firefox driver")
        return driver

    except Exception as firefox_error:
        print(f"❌ Firefox không khả dụng: {str(firefox_error)[:100]}")

        # Try Chrome as fallback
        try:
            print("🔄 Thử Chrome driver...")
            chrome_options = webdriver.ChromeOptions()

            if app_settings['headless']:
                chrome_options.add_argument('--headless')

            # Basic Chrome options
            chrome_options.add_argument(f'--user-agent={user_agent}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(options=chrome_options)

            # Set conservative timeouts
            driver.implicitly_wait(5)
            driver.set_page_load_timeout(20)

            print("🌐 Sử dụng Chrome driver")
            return driver

        except Exception as chrome_error:
            print(f"❌ Chrome cũng không khả dụng: {str(chrome_error)[:100]}")

            # Last resort: try basic Firefox without options
            try:
                print("🔄 Thử Firefox cơ bản...")
                basic_options = Options()
                if app_settings['headless']:
                    basic_options.add_argument('--headless')

                driver = webdriver.Firefox(options=basic_options)
                driver.implicitly_wait(5)
                driver.set_page_load_timeout(15)

                print("🦊 Sử dụng Firefox cơ bản")
                return driver

            except Exception as basic_error:
                print(f"❌ Tất cả driver đều thất bại: {str(basic_error)[:100]}")
                raise Exception("Không thể tạo bất kỳ webdriver nào. Vui lòng kiểm tra Firefox/Chrome đã cài đặt chưa.")

def normalize_url(url):
    """Normalize URL to handle redirects between different domains"""
    if url.endswith('/'):
        url = url[:-1]
    
    # Convert old domains to new domain
    url = url.replace('metruyencv.com', 'metruyencv.biz')
    url = url.replace('metruyencv.info', 'metruyencv.biz')
    
    return url

async def get_novel_info_with_redirect(novel_url):
    """Get novel info handling redirects"""
    normalized_url = normalize_url(novel_url)
    
    try:
        print(f"🔍 Trying to fetch: {normalized_url}")
        response = await client.get(normalized_url, headers=header)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Try to find novel info
        title_elem = soup.find('h1', class_='mb-2')
        if not title_elem:
            title_elem = soup.find('h1')
        
        if not title_elem:
            raise Exception("Could not find novel title")
            
        title = str(title_elem.text).strip()
        
        # Find author
        author_elem = soup.find('a', class_='text-gray-500')
        if not author_elem:
            author_elem = soup.find('a', string=lambda text: text and 'tác giả' in text.lower())
        author = str(author_elem.text).strip() if author_elem else "Unknown"
        
        # Find status
        status_elem = soup.find('a', class_='inline-flex border border-primary rounded px-2 py-1 text-primary')
        if status_elem:
            status_span = status_elem.find('span')
            status = str(status_span.text).strip() if status_span else "Unknown"
        else:
            status = "Unknown"
        
        # Find attribute/genre
        attr_elem = soup.find('a', class_='inline-flex border border-rose-700 dark:border-red-400 rounded px-2 py-1 text-rose-700 dark:text-red-400')
        attribute = str(attr_elem.text).strip() if attr_elem else "Unknown"
        
        # Find image
        img_elem = soup.find('img', class_='w-44 h-60 shadow-lg rounded mx-auto')
        if not img_elem:
            img_elem = soup.find('img', alt=lambda x: x and 'cover' in x.lower())
        image_url = img_elem['src'] if img_elem else None
        
        return {
            'title': title,
            'author': author, 
            'status': status,
            'attribute': attribute,
            'image_url': image_url,
            'final_url': normalized_url
        }
        
    except Exception as e:
        print(f"❌ Error fetching novel info: {e}")
        return None

def sort_chapters(list_of_chapters):
    """Sort chapters by chapter number"""
    lst = len(list_of_chapters)
    for i in range(0, lst):
        for j in range(0, lst - i - 1):
            if (list_of_chapters[j][2] > list_of_chapters[j + 1][2]):
                temp = list_of_chapters[j]
                list_of_chapters[j] = list_of_chapters[j + 1]
                list_of_chapters[j + 1] = temp
    return list_of_chapters

async def get_chapter_with_selenium(chapter_number, novel_url):
    """Get chapter content using Selenium with httpx fallback"""
    base_url = novel_url.replace('/truyen/', '/truyen/').rstrip('/')
    url = f'{base_url}/chuong-{chapter_number}'

    # Add delay between requests
    if app_settings['request_delay'] > 0:
        await asyncio.sleep(app_settings['request_delay'])

    print(f"🔍 Tải chapter {chapter_number}...")

    # Try Selenium first
    try:
        result = await get_chapter_with_selenium_browser(chapter_number, novel_url)
        if result:
            return result
    except Exception as selenium_error:
        print(f"⚠️  Selenium thất bại: {str(selenium_error)[:100]}")

    # Fallback to httpx if Selenium fails
    print(f"🔄 Fallback: Thử httpx cho chapter {chapter_number}...")
    try:
        response = await client.get(url, headers=header)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # Try to find chapter content
        chapter_content = None
        content_selectors = [
            ('div', {'id': 'chapter-content'}),
            ('div', {'class': 'break-words'}),
            ('main', {}),
            ('article', {})
        ]

        for tag, attrs in content_selectors:
            chapter_content = soup.find(tag, attrs)
            if chapter_content:
                text_content = chapter_content.get_text(strip=True)
                if len(text_content) > 50:
                    break
                else:
                    chapter_content = None

        if chapter_content:
            # Get title
            title_elem = soup.find('h1') or soup.find('h2')
            chapter_title = str(title_elem) if title_elem else f"<h2>Chương {chapter_number}</h2>"

            html = str(chapter_content)
            print(f"✅ Httpx thành công cho chapter {chapter_number}")
            return chapter_title, html, chapter_number
        else:
            print(f"❌ Httpx không tìm thấy content cho chapter {chapter_number}")

    except Exception as httpx_error:
        print(f"❌ Httpx cũng thất bại: {str(httpx_error)[:100]}")

    # Both methods failed
    print(f"💥 Tất cả methods thất bại cho chapter {chapter_number}")
    missing_chapter.append((f"Chương {chapter_number}", url, chapter_number))
    return None

async def get_chapter_with_selenium_browser(chapter_number, novel_url):
    """Get chapter content using Selenium browser with robust error handling"""
    base_url = novel_url.replace('/truyen/', '/truyen/').rstrip('/')
    url = f'{base_url}/chuong-{chapter_number}'

    driver = None
    try:
        driver = get_selenium_driver()
        print(f"🌐 Đang truy cập: {url}")

        # Set page load timeout
        driver.set_page_load_timeout(30)

        try:
            driver.get(url)
        except Exception as e:
            print(f"⚠️  Lỗi load page: {e}")
            # Try to continue anyway

        # Wait for page to load with shorter sleep
        await asyncio.sleep(2)

        print(f"🔍 Đang tìm nội dung chapter {chapter_number}...")

        # Simplified selectors that are more likely to work
        content_selectors = [
            (By.ID, 'chapter-content'),
            (By.CLASS_NAME, 'break-words'),
            (By.TAG_NAME, 'main'),
            (By.TAG_NAME, 'article'),
            (By.CSS_SELECTOR, 'div.content'),
            (By.CSS_SELECTOR, 'div p')
        ]

        chapter_content = None
        for i, (by, selector) in enumerate(content_selectors):
            try:
                print(f"  🔎 Thử selector {i+1}: {selector}")

                # Use shorter timeout for each selector
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )

                if element:
                    text_content = element.text.strip()
                    print(f"  📝 Tìm thấy element, độ dài text: {len(text_content)}")

                    if len(text_content) > 50:
                        chapter_content = element
                        print(f"  ✅ Chọn selector {i+1} - Nội dung đủ dài")
                        break
                    elif len(text_content) > 10:
                        # Keep as backup if no better content found
                        if not chapter_content:
                            chapter_content = element
                            print(f"  📝 Backup selector {i+1} - Nội dung ngắn")

            except TimeoutException:
                print(f"  ⏰ Timeout với selector {i+1}")
                continue
            except Exception as e:
                print(f"  ❌ Lỗi với selector {i+1}: {str(e)[:100]}")
                continue

        if not chapter_content:
            print(f"❌ Không tìm thấy nội dung cho chapter {chapter_number}")
            try:
                print(f"📄 Page title: {driver.title}")
                print(f"📄 Page URL: {driver.current_url}")

                # Check if page loaded at all
                page_source = driver.page_source
                if len(page_source) < 1000:
                    print(f"⚠️  Page source quá ngắn: {len(page_source)} chars")
                elif "404" in page_source or "not found" in page_source.lower():
                    print(f"❌ Chapter {chapter_number} không tồn tại (404)")
                else:
                    print(f"📄 Page source length: {len(page_source)} chars")

            except Exception as debug_e:
                print(f"⚠️  Không thể debug page: {debug_e}")

            missing_chapter.append((f"Chương {chapter_number}", url, chapter_number))
            return None

        print(f"📖 Đang lấy title và content cho chapter {chapter_number}...")

        # Get title with simpler approach
        chapter_title = f"Chương {chapter_number}"
        try:
            title_elem = driver.find_element(By.TAG_NAME, 'h1')
            if title_elem and title_elem.text.strip():
                chapter_title = f"<h2>{title_elem.text.strip()}</h2>"
                print(f"📝 Tìm thấy title: {title_elem.text.strip()}")
        except:
            try:
                title_elem = driver.find_element(By.TAG_NAME, 'h2')
                if title_elem and title_elem.text.strip():
                    chapter_title = f"<h2>{title_elem.text.strip()}</h2>"
                    print(f"📝 Tìm thấy title h2: {title_elem.text.strip()}")
            except:
                print(f"📝 Sử dụng title mặc định: {chapter_title}")

        # Get content HTML with error handling
        try:
            html = chapter_content.get_attribute('outerHTML')
            print(f"📄 Độ dài HTML: {len(html)} ký tự")
        except Exception as e:
            print(f"⚠️  Lỗi lấy HTML: {e}")
            # Fallback to innerHTML
            try:
                html = chapter_content.get_attribute('innerHTML')
                html = f'<div>{html}</div>'
                print(f"📄 Fallback innerHTML: {len(html)} ký tự")
            except Exception as e2:
                print(f"❌ Không thể lấy content: {e2}")
                return None

        # Simple HTML cleanup
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Remove only the most problematic elements
            for unwanted in soup.find_all(['script', 'style', 'noscript']):
                unwanted.decompose()

            html = str(soup)
        except Exception as e:
            print(f"⚠️  Lỗi cleanup HTML: {e}")
            # Continue with original HTML

        # Skip OCR for now to avoid complications
        # OCR can be added back later if needed

        # Final content check
        try:
            final_soup = BeautifulSoup(html, 'lxml')
            final_text = final_soup.get_text(strip=True)
            print(f"✅ Chapter {chapter_number} hoàn thành - {len(final_text)} ký tự text")

            if len(final_text) < 10:
                print(f"⚠️  Nội dung quá ngắn, có thể không đúng")

        except Exception as e:
            print(f"⚠️  Lỗi kiểm tra final content: {e}")

        return chapter_title, html, chapter_number

    except asyncio.CancelledError:
        print(f"⚠️  Task bị cancel cho chapter {chapter_number}")
        return None
    except Exception as e:
        print(f"❌ Lỗi tổng quát chapter {chapter_number}: {str(e)[:200]}")
        missing_chapter.append((f"Chương {chapter_number}", url, chapter_number))
        return None
    finally:
        # Safe driver cleanup
        if driver:
            try:
                driver.quit()
                print(f"🔧 Đã đóng driver cho chapter {chapter_number}")
            except Exception as cleanup_e:
                print(f"⚠️  Lỗi đóng driver: {cleanup_e}")
                # Force kill if needed
                try:
                    driver.service.stop()
                except:
                    pass

@alru_cache(maxsize=1024)
async def fetch_chapters(start_chapter, end_chapter, novel_url):
    """Fetch chapters with progress bar"""
    tasks = [get_chapter_with_selenium(number, novel_url) for number in range(start_chapter, end_chapter + 1)]
    chapters = []

    # Use tqdm to display progress bar
    async for future in tqdm(asyncio.as_completed(tasks), total=end_chapter - start_chapter + 1,
                            desc="📚 Tải chapters...", unit=" chapters"):
        chapter = await future
        if chapter is not None:
            chapters.append(chapter)

    chapters = delete_dupe(chapters)
    sorted_chapters = sort_chapters(chapters)
    return sorted_chapters

def create_epub(title, author, status, attribute, image, chapters, path, filename):
    """Create EPUB file from chapters"""
    book = epub.EpubBook()
    book.set_title(title)
    book.set_identifier("nguyentd010")
    book.add_author(author)
    book.set_language('vn')
    book.add_metadata(None, 'meta', '', {'name': 'status', 'content': status})
    book.add_metadata(None, 'meta', '', {'name': 'chapter', 'content': str(len(chapters))})
    book.set_cover(content=image, file_name='cover.jpg')
    book.add_metadata(None, 'meta', '', {'name': 'attribute', 'content': attribute})

    p = 1
    chapter_num = []
    for chapter_title, chapter, i in chapters:
        chapter_num.append(i)
        chapter_title = BeautifulSoup(chapter_title, 'lxml').text
        chapter = f'<h2>{chapter_title}</h2>' + "<h3>Generated by nguyentd010's metruyencv_downloader</h3>" + chapter

        c1 = epub.EpubHtml(title=chapter_title, file_name=f'chap_{i}.xhtml', lang='vn')
        c1.content = chapter
        book.add_item(c1)
        p += 1

    # Define Table of Contents
    book.toc = tuple(book.get_items_of_type(epub.EpubHtml))

    # Add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Basic spine
    book.spine = ['nav'] + list(book.get_items_of_type(epub.EpubHtml))

    # Write to file
    epub.write_epub(f'{path}/{filename}.epub', book, {})
    print(f'📖 Đã tạo file EPUB: {path}/{filename}.epub')

async def main():
    """Main function"""
    print("🚀 MeTruyenCV Downloader with Config Management")
    print("=" * 60)

    # Display current config
    config.display_config()

    while True:
        global missing_chapter
        missing_chapter = []  # Reset missing chapters for each run

        print("\n" + "="*60)

        # Check if should auto run
        auto_run_info = config.get_auto_run_info()
        if auto_run_info:
            print("🤖 AUTO RUN MODE - Chạy tự động theo config")
            novel_url = auto_run_info['url']
            start_chapter = auto_run_info['start_chapter']
            end_chapter = auto_run_info['end_chapter']
            print(f"📖 Novel: {novel_url}")
            print(f"📄 Chapters: {start_chapter} - {end_chapter}")
        else:
            # Get novel input with smart defaults
            novel_input = config.get_novel_input_with_defaults()
            novel_url = novel_input['url']
            start_chapter = novel_input['start_chapter']
            end_chapter = novel_input['end_chapter']

        # Normalize URL to handle redirects
        novel_url = normalize_url(novel_url)
        print(f"🔗 Normalized URL: {novel_url}")

        # Validate URL
        if 'metruyencv' not in novel_url:
            print("❌ Lỗi: URL phải từ metruyencv")
            print("📝 Ví dụ: https://metruyencv.biz/truyen/ten-truyen")
            continue

        # Get novel information
        novel_info = await get_novel_info_with_redirect(novel_url)
        if not novel_info:
            print("❌ Không thể lấy thông tin truyện")
            continue

        print(f"\n📖 Truyện: {novel_info['title']}")
        print(f"✍️  Tác giả: {novel_info['author']}")
        print(f"📊 Trạng thái: {novel_info['status']}")

        # Download cover image
        image = None
        if novel_info['image_url']:
            try:
                image_response = await client.get(novel_info['image_url'], headers=header)
                image_response.raise_for_status()
                image = image_response.content
                print("✅ Đã tải ảnh bìa")
            except Exception as e:
                print(f"⚠️  Không thể tải ảnh bìa: {e}")
                image = b''  # Empty image
        else:
            image = b''

        # Create output directory
        filename = novel_url.split('/')[-1].replace('-', '')
        path = f"{disk}:/{download_settings['folder']}/{novel_info['title'].replace(':', ',').replace('?', '')}"
        os.makedirs(path, exist_ok=True)

        # Download chapters
        print(f"\n🚀 Bắt đầu tải {end_chapter - start_chapter + 1} chapters...")
        chapters = await fetch_chapters(start_chapter, end_chapter, novel_info['final_url'])
        valid_chapters = [chapter for chapter in chapters if chapter is not None]

        if valid_chapters:
            create_epub(novel_info['title'], novel_info['author'], novel_info['status'],
                       novel_info['attribute'], image, valid_chapters, path, filename)
            print(f'✅ Tải thành công {len(valid_chapters)}/{end_chapter - start_chapter + 1} chapter.')
            print(f'📁 File của bạn nằm tại: "{path}"')

            # Save last novel info for next time
            config.save_last_novel_info(novel_url, start_chapter, end_chapter)
            print("💾 Đã lưu thông tin novel để sử dụng lần sau")

            # Auto-enable auto_run mode after successful download
            if not config.should_auto_run():
                config.enable_auto_run()
                print("🤖 Đã tự động bật chế độ AUTO RUN - Lần sau sẽ tự động tiếp tục")
        else:
            print("❌ Lỗi. Tải không thành công")

        # Ask to continue or change mode
        if config.should_auto_run():
            continue_choice = input("\n🔄 Tiếp tục auto run? (y/n/manual): ").lower()
            if continue_choice == 'n':
                break
            elif continue_choice == 'manual':
                config.disable_auto_run()
                print("🔄 Chuyển sang chế độ manual - Lần sau sẽ hỏi input")
        else:
            if input("\n🔄 Tải tiếp? (y/n): ").lower() != 'y':
                break

        # Clear cache and missing chapters for next run
        missing_chapter.clear()
        fetch_chapters.cache_clear()

if __name__ == '__main__':
    asyncio.run(main())
