import httpx
from bs4 import BeautifulSoup
from ebooklib import epub
import asyncio
from user_agent import get
import warnings
# Suppress ebooklib warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib")
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



# Enable garbage collection
gc.enable()

data_dir = user_config_dir(appname='metruyencv-downloader',appauthor='nguyentd010')
os.makedirs(data_dir, exist_ok=True)
if not os.path.isfile(data_dir + '\\config.ini'):
    config = configparser.ConfigParser()
    with open(data_dir + '\\config.ini', 'w') as configfile:
        config.write(configfile)

missing_chapter = []
if os.stat(data_dir+"\\config.ini").st_size == 0:
    username = str(input('Email tài khoản metruyencv?:'))
    password = str(input('Password?:'))
    disk = str(input('Ổ đĩa lưu truyện(C/D):')).capitalize()
    max_connections = int(input('''Max Connections (10 -> 1000) 
    Note: Càng cao thì rủi ro lỗi cũng tăng, chỉ số tối ưu nhất là 50 : '''))
    save = str(input('Lưu config?(Y/N):')).capitalize()

else:
    config = configparser.ConfigParser()
    config.read(data_dir + '\\config.ini')
    username = str(config.get('data', 'login'))
    password = str(config.get('data', 'password'))
    disk = str(config.get('data', 'disk'))
    max_connections = int(config.get('data', 'max-connection'))
    save = None


limits = httpx.Limits(max_keepalive_connections=100, max_connections=max_connections)
timeout = httpx.Timeout(None)
client = httpx.AsyncClient(limits=limits, timeout=timeout)

# Base URL for the novel
BASE_URL = 'https://metruyencv.com/truyen/'

user_agent = get()

file_location = os.getcwd()


pytesseract.pytesseract.tesseract_cmd = fr'{file_location}\Tesseract-OCR\tesseract.exe'

header = {'user-agent': user_agent}

if save == 'Y':
    config = configparser.ConfigParser()
    config['data'] = {'login': username, 'password': password, 'disk' : disk, 'max-connection' : max_connections}

    # Write the configuration to a file
    with open(data_dir + '\\config.ini', 'w') as configfile:
        config.write(configfile)

def ocr(image: bytes) -> str:
    image = Image.open(io.BytesIO(image))
    image = image.convert('L')
    text = pytesseract.image_to_string(image, lang='vie')
    return text

def delete_dupe(list):
    list1 = list.copy()
    l = []
    num = 0
    for i, j, k in list1:
        if k in l:
            del list1[num]
        l.append(i)
        num += 1
    return list1

async def handle_route(route):
  if "https://googleads" in route.request.url or "https://adclick" in route.request.url:
    await route.abort()
  else:
    await route.continue_()


async def download_missing_chapter(links):
    results = []
    setting = True
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto('https://metruyencv.com/', timeout=30000)

            # Try to find and click login button with multiple selectors
            login_selectors = [
                'button:has-text("Đăng nhập")',
                'button:text("Đăng nhập")',
                'xpath=/html/body/div[1]/header/div/div/div[3]/button',
                'button[class*="login"]',
                'a[href*="login"]',
                'button'  # Fallback to any button and check text
            ]

            login_clicked = False
            for selector in login_selectors:
                try:
                    if selector == 'button':  # Special handling for fallback
                        buttons = await page.query_selector_all('button')
                        for button in buttons:
                            text = await button.inner_text()
                            if 'đăng nhập' in text.lower().strip():
                                await button.click()
                                login_clicked = True
                                print("Đã click vào nút đăng nhập")
                                break
                        if login_clicked:
                            break
                    else:
                        await page.locator(selector).click(timeout=5000)
                        login_clicked = True
                        print("Đã click vào nút đăng nhập")
                        break
                except:
                    continue

            if not login_clicked:
                print("Không thể tìm thấy nút đăng nhập, thử truy cập trực tiếp")
                # Try direct login page access
                await page.goto('https://metruyencv.com/login', timeout=30000)

            await asyncio.sleep(2)

            # Try to fill login form with multiple selectors
            username_selectors = [
                'xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[1]/div[2]/input',
                'input[type="email"]',
                'input[placeholder*="email"]',
                'input[name*="email"]',
                'input[id*="email"]'
            ]

            password_selectors = [
                'xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[2]/div[2]/input',
                'input[type="password"]',
                'input[placeholder*="password"]',
                'input[name*="password"]',
                'input[id*="password"]'
            ]

            # Fill username
            username_filled = False
            for selector in username_selectors:
                try:
                    await page.locator(selector).fill(username, timeout=5000)
                    username_filled = True
                    print("Đã điền username")
                    break
                except:
                    continue

            if not username_filled:
                print("Không thể điền username")
                await browser.close()
                return results

            await asyncio.sleep(1)

            # Fill password
            password_filled = False
            for selector in password_selectors:
                try:
                    await page.locator(selector).fill(password, timeout=5000)
                    password_filled = True
                    print("Đã điền password")
                    break
                except:
                    continue

            if not password_filled:
                print("Không thể điền password")
                await browser.close()
                return results

            await asyncio.sleep(1)

            # Try to submit login form
            submit_selectors = [
                'xpath=/html/body/div[1]/div[3]/div[2]/div/div/div[2]/div[3]/div[1]/button',
                'button[type="submit"]',
                'button:has-text("Đăng nhập")',
                'input[type="submit"]'
            ]

            submit_clicked = False
            for selector in submit_selectors:
                try:
                    await page.locator(selector).click(timeout=5000)
                    submit_clicked = True
                    print("Đã submit form đăng nhập")
                    break
                except:
                    continue

            if not submit_clicked:
                print("Không thể submit form đăng nhập")
                await browser.close()
                return results

            await asyncio.sleep(3)

            # Check if login was successful by looking for user menu or profile
            try:
                await page.wait_for_selector('button:has-text("Tài khoản"), a:has-text("Tài khoản"), [class*="user"], [class*="profile"]', timeout=10000)
                print("Đăng nhập thành công")
            except:
                print("Có thể đăng nhập không thành công, tiếp tục thử...")

        except Exception as e:
            print(f"Lỗi trong quá trình đăng nhập: {e}")
            print("Tiếp tục với việc tải chapter...")

        for title, link, num in links:
            try:
                print(f"Đang tải chapter {num}...")
                await page.goto(link, timeout=30000)
                await page.route("**/*", handle_route)

                # Configure reading settings if first time
                if setting:
                    try:
                        # Try to find and click settings button
                        settings_selectors = [
                            'xpath=/html/body/div[1]/main/div[3]/div[1]/button[1]',
                            'button:has-text("Cài đặt")',
                            'button[class*="setting"]',
                            '[class*="setting"] button'
                        ]

                        for selector in settings_selectors:
                            try:
                                await page.locator(selector).click(timeout=5000)
                                print("Đã mở cài đặt đọc")
                                break
                            except:
                                continue

                        await asyncio.sleep(1)

                        # Try to set font
                        font_selectors = [
                            'xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[3]/select',
                            'select[class*="font"]',
                            'select option[value*="Times"]'
                        ]

                        for selector in font_selectors:
                            try:
                                await page.locator(selector).select_option(value='Times New Roman', timeout=5000)
                                print("Đã chọn font Times New Roman")
                                break
                            except:
                                continue

                        # Try to set font size
                        size_selectors = [
                            'xpath=/html/body/div[1]/main/div[3]/div[2]/div/div[2]/div/div/div[2]/div[4]/select',
                            'select[class*="size"]'
                        ]

                        for selector in size_selectors:
                            try:
                                await page.locator(selector).select_option(value='50px', timeout=5000)
                                print("Đã chọn font size 50px")
                                break
                            except:
                                continue

                        await page.reload()
                        setting = False

                    except Exception as e:
                        print(f"Không thể cài đặt font: {e}")
                        setting = False

                # Try to get chapter content with multiple selectors
                content_selectors = [
                    'xpath=/html/body/div[1]/main/div[4]/div[1]',
                    '#chapter-content',
                    '[class*="chapter-content"]',
                    '[class*="content"]',
                    'main [class*="text"]'
                ]

                missing_html1 = ""
                for selector in content_selectors:
                    try:
                        loadmore_element1 = await page.wait_for_selector(selector, state='attached', timeout=10000)
                        missing_html1 = await loadmore_element1.inner_html()
                        missing_html1 = str(missing_html1)
                        if len(missing_html1.strip()) > 50:  # Check if content is substantial
                            print(f"Đã lấy được nội dung chapter {num}")
                            break
                    except:
                        continue

                if not missing_html1 or len(missing_html1.strip()) < 50:
                    print(f"Không thể lấy nội dung chapter {num}")
                    continue

                # Check if content is too short, try to get additional content
                if missing_html1.count('<br><br>') <= 4:
                    try:
                        additional_selectors = [
                            'xpath=/html/body/div[1]/main/div[4]/div[3]',
                            '[class*="chapter-content"] + div',
                            '[class*="content"] + div'
                        ]

                        for selector in additional_selectors:
                            try:
                                loadmore_element2 = await page.wait_for_selector(selector, state='attached', timeout=5000)
                                missing_html2 = await loadmore_element2.inner_html()
                                missing_html2 = BeautifulSoup(str(missing_html2), 'lxml')

                                # Handle canvas elements (OCR)
                                if missing_html2.find('canvas') is not None:
                                    images = await page.query_selector_all('canvas')
                                    for image in images:
                                        try:
                                            image_bytes = await image.screenshot()
                                            ocr_result = ocr(image_bytes)
                                            missing_html2.find('canvas').replace_with(ocr_result)
                                        except Exception as e:
                                            print(f"Lỗi OCR: {e}")

                                missing_html1 = missing_html1 + '<br/><br/>' + str(missing_html2)
                                break
                            except:
                                continue
                    except Exception as e:
                        print(f"Không thể lấy nội dung bổ sung: {e}")

                # Clean up HTML
                missing_html1 = missing_html1.replace('<br/><br/>', '<br/>').replace('<br/>', '<br/><br/>').replace('\n', ' ')
                results.append((title, missing_html1, num))
                print(f'Đã tải xong chapter {num}')

            except Exception as e:
                print(f"Lỗi khi tải chapter {num}: {e}")
                continue

        await browser.close()
    return results


def sort_chapters(list_of_chapters):
    lst = len(list_of_chapters)
    for i in range(0, lst):
        for j in range(0, lst - i - 1):
            if (list_of_chapters[j][2] > list_of_chapters[j + 1][2]):
                temp = list_of_chapters[j]
                list_of_chapters[j] = list_of_chapters[j + 1]
                list_of_chapters[j + 1] = temp
    return list_of_chapters


# Retry decorator for handling transient errors, excluding 404 errors

async def get_chapter_with_retry(chapter_number, novel_url):
    """Get chapter content using Playwright for JavaScript-rendered content"""
    url = f'{novel_url}/chuong-{chapter_number}'

    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            page = await browser.new_page()

            # Set user agent
            await page.set_extra_http_headers(header)

            # Navigate to chapter page
            await page.goto(url, timeout=30000)

            # Wait for content to load with multiple strategies
            content_loaded = False
            wait_strategies = [
                "document.querySelector('#chapter-content') && document.querySelector('#chapter-content').innerText.length > 100",
                "document.querySelector('[class*=\"chapter-content\"]') && document.querySelector('[class*=\"chapter-content\"]').innerText.length > 100",
                "document.querySelector('[class*=\"content\"]') && document.querySelector('[class*=\"content\"]').innerText.length > 100",
                "document.querySelector('main') && document.querySelector('main').innerText.length > 200"
            ]

            for strategy in wait_strategies:
                try:
                    await page.wait_for_function(strategy, timeout=10000)
                    content_loaded = True
                    break
                except:
                    continue

            if not content_loaded:
                print(f"Timeout waiting for chapter {chapter_number} content to load")
                # Wait a bit more and try to get whatever content is available
                await asyncio.sleep(3)

            # Get page content after JavaScript execution
            content = await page.content()
            await browser.close()

            # Parse the rendered HTML
            soup = BeautifulSoup(content, 'lxml')

            # Try to find chapter content with multiple selectors
            chapter_content = None
            content_selectors = [
                ('div', {'id': 'chapter-content'}),
                ('div', {'class': 'break-words'}),
                ('div', {'class': lambda x: x and 'chapter-content' in x}),
                ('div', {'class': lambda x: x and 'content' in x}),
                ('main', {}),
                ('article', {})
            ]

            for tag, attrs in content_selectors:
                chapter_content = soup.find(tag, attrs)
                if chapter_content:
                    text_content = chapter_content.get_text(strip=True)
                    if len(text_content) > 100:  # Check if content is substantial
                        break
                    else:
                        chapter_content = None

            # Try to find chapter title with multiple selectors
            title_selectors = ['h1', 'h2', 'h3', '[class*="title"]', '[class*="chapter"]']
            chapter_title_elem = None

            for selector in title_selectors:
                if selector.startswith('['):
                    # CSS selector
                    chapter_title_elem = soup.select_one(selector)
                else:
                    # Tag selector
                    chapter_title_elem = soup.find(selector)
                if chapter_title_elem:
                    break

            chapter_title = str(chapter_title_elem) if chapter_title_elem else f"Chương {chapter_number}"

            if chapter_content:
                html = str(chapter_content)
                # Check if content is substantial
                text_content = chapter_content.get_text(strip=True)
                if len(text_content) > 100:
                    return chapter_title, html, chapter_number

            print(f"Không thể tải nội dung chapter {chapter_number}")
            missing_chapter.append((chapter_title, url, chapter_number))
            return None

    except Exception as e:
        print(f"Error fetching chapter {chapter_number}: {e}")
        missing_chapter.append((f"Chương {chapter_number}", url, chapter_number))
        return None

# Cache the results of the 'get' function for better performance
@alru_cache(maxsize=1024)
async def fetch_chapters(start_chapter, end_chapter, novel_url):
    tasks1 = [get_chapter_with_retry(number, novel_url) for number in range(start_chapter, end_chapter + 1)]
    chapters = []
    # Use tqdm to display a progress bar
    async for future1 in tqdm(asyncio.as_completed(tasks1), total=end_chapter - start_chapter + 1, desc="Tải chapters...",
                             unit=" chapters"):
        chapter = await future1  # Await here to get the actual result
        if chapter is not None:
            chapters.append(chapter)
    print('Đang tải chapters bị thiếu...')
    if missing_chapter != []:
        chapters += await download_missing_chapter(missing_chapter)
    chapters = delete_dupe(chapters)
    sorted_chapters = sort_chapters(chapters)
    return sorted_chapters


def create_epub(title, author, status, attribute, image, chapters, path, filename):
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
        if p == 1:
            chapter = f"<h1>{title}</h1>" + chapter
        p += 1
        html = BeautifulSoup(chapter, 'lxml')
        file_name = f'chapter{i}-{chapter_title}.html'
        chapter = epub.EpubHtml(lang='vn', title=chapter_title, file_name=file_name, uid=f'chapter{i}')
        chapter.content = str(html)
        book.add_item(chapter)

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

    book.spine = [f'chapter{i}' for i in chapter_num]
    epub.write_epub(f'{path}/{filename}.epub', book)


async def main():
    while True:
        global missing_chapter
        missing_chapter = []  # Reset missing chapters for each run

        novel_url = input('Nhập link metruyencv mà bạn muốn tải: ')

        # Auto-convert from .info to .com (since .info redirects to .com)
        if 'metruyencv.info' in novel_url:
            novel_url = novel_url.replace('metruyencv.info', 'metruyencv.com')
            print(f"Đã chuyển đổi URL sang: {novel_url}")

        # Validate URL
        if 'metruyencv.com' not in novel_url:
            print("❌ Lỗi: URL phải từ metruyencv.com")
            print("Ví dụ: https://metruyencv.com/truyen/ten-truyen")
            continue

        if '/' == novel_url[-1]:
            novel_url = novel_url[:-1]
        start_chapter = int(input('Chapter bắt đầu: '))
        end_chapter = int(input('Chapter kết thúc: '))

        try:
            response = await client.get(novel_url, headers=header)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            title = str(soup.find('h1', class_='mb-2').text)
            author = str(soup.find('a', class_='text-gray-500').text).strip()
            status = str(
                soup.find('a', class_='inline-flex border border-primary rounded px-2 py-1 text-primary').select_one(
                    'span').text).strip()
            attribute = str(soup.find('a',
                                      class_='inline-flex border border-rose-700 dark:border-red-400 rounded px-2 py-1 text-rose-700 dark:text-red-400').text)
            image_url = soup.find('img', class_='w-44 h-60 shadow-lg rounded mx-auto')['src']
        except (httpx.HTTPError, TypeError, KeyError) as e:
            print(f"Error fetching novel information: {e}")
            continue

        try:
            image_data = await client.get(image_url, headers=header)
            image_data.raise_for_status()
            image = image_data.content
        except httpx.HTTPError as e:
            print(f"Error downloading image: {e}")
            continue

        filename = novel_url.replace(BASE_URL, '').replace('-', '')
        path = f"{disk}:/novel/{title.replace(':', ',').replace('?', '')}"
        os.makedirs(path, exist_ok=True)

        chapters = await fetch_chapters(start_chapter, end_chapter, novel_url)
        valid_chapters = [chapter for chapter in chapters if chapter is not None]

        if valid_chapters:
            create_epub(title, author, status, attribute, image, valid_chapters, path, filename)
            print(
                f'Tải thành công {len(valid_chapters)}/{end_chapter - start_chapter + 1} chapter. File của bạn nằm tại "{path}"')
        else:
            print("Lỗi. Tải không thành công")

        if input("Tải tiếp? (y/n): ").lower() != 'y':
            break

        # Clear cache and missing chapters for next run
        missing_chapter.clear()
        fetch_chapters.cache_clear()


if __name__ == '__main__':
    asyncio.run(main())
