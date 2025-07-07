import httpx
import asyncio
from bs4 import BeautifulSoup
import json
from logger import setup_logger
import time
import signal
import sys

# Initialize logger
logger = setup_logger('mtc_structure_checker')

# Global flag to track shutdown state
is_shutting_down = False

# Signal handler for graceful shutdown
def handle_shutdown_signal(signum, frame):
    global is_shutting_down
    logger.warning(f"Received signal {signum}. Starting graceful shutdown...")
    is_shutting_down = True
    # Close all tasks - we'll handle this in the main function

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

async def check_structure():
    global is_shutting_down
    
    logger.info("Starting website structure check")
    start_time = time.time()
    
    url = "https://metruyencv.com/truyen/dai-duong-chi-toi-nguu-vuong-gia/chuong-1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    logger.debug(f"Using URL: {url}")
    logger.debug(f"Using headers: {headers}")
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            if is_shutting_down:
                logger.warning("Shutdown requested, cancelling structure check")
                return
                
            logger.info(f"Đang tải trang {url}...")
            request_start = time.time()
            
            try:
                response = await client.get(url, headers=headers)
                request_time = time.time() - request_start
                
                logger.info(f"Đã tải xong trong {request_time:.2f} giây. Trạng thái: {response.status_code}")
                response.raise_for_status()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error when loading page: {e}")
                return
                
            if is_shutting_down:
                logger.warning("Shutdown requested after page load, cancelling analysis")
                return
            
            logger.debug("Parsing page content with BeautifulSoup")
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Kiểm tra tiêu đề chương
            logger.info("Kiểm tra tiêu đề chương")
            chapter_title = soup.find('h2', class_='text-center text-gray-600 dark:text-gray-400 text-balance')
            if chapter_title:
                logger.info(f"Tìm thấy tiêu đề: {chapter_title.text.strip()}")
            else:
                logger.warning("Không tìm thấy tiêu đề với bộ chọn hiện tại")
                # Tìm kiếm các h2 khác
                other_h2 = soup.find_all('h2')
                logger.info(f"Số lượng thẻ h2 khác: {len(other_h2)}")
                for i, h2 in enumerate(other_h2[:3]):  # Hiển thị 3 thẻ h2 đầu tiên
                    logger.debug(f"H2 #{i+1}: {h2}")
                    print(f"H2 #{i+1}: {h2}")
            
            # Check for shutdown
            if is_shutting_down:
                logger.warning("Shutdown requested, stopping analysis")
                return
                
            # Kiểm tra nội dung chương
            logger.info("Kiểm tra nội dung chương")
            content_div = soup.find('div', class_='break-words')
            if content_div:
                content_text = content_div.text.strip()
                logger.info(f"Nội dung: {content_text[:100]}... (hiển thị 100 ký tự đầu tiên)")
                logger.info(f"Số ký tự: {len(content_text)}")
                print(f"Nội dung: {content_text[:100]}... (hiển thị 100 ký tự đầu tiên)")
                print(f"Số ký tự: {len(content_text)}")
            else:
                logger.warning("Không tìm thấy nội dung với bộ chọn hiện tại")
                print("Không tìm thấy nội dung với bộ chọn hiện tại")
                
            # Check for shutdown
            if is_shutting_down:
                logger.warning("Shutdown requested, stopping div search")
                return
                
            # Tìm tất cả các div có class name chứa từ khóa "content", "chapter", "text"
            logger.info("Tìm kiếm các div tiềm năng chứa nội dung")
            potential_content_divs = []
            all_divs = soup.find_all('div')
            logger.debug(f"Tìm thấy {len(all_divs)} thẻ div trong trang")
            
            for div in all_divs:
                if is_shutting_down:
                    break
                
                class_names = div.get('class', [])
                for class_name in class_names:
                    if any(keyword in class_name.lower() for keyword in ['content', 'chapter', 'text', 'word']):
                        text_content = div.text.strip()
                        if len(text_content) > 500:  # Chỉ xem xét các div có nhiều nội dung
                            logger.debug(f"Tìm thấy div có class {class_names} với nội dung dài {len(text_content)}")
                            potential_content_divs.append({
                                'classes': class_names,
                                'text_length': len(text_content),
                                'sample': text_content[:50] + '...'
                            })
            
            print("\nCác div tiềm năng chứa nội dung:")
            logger.info(f"Tìm thấy {len(potential_content_divs)} div tiềm năng chứa nội dung")
            for i, div_info in enumerate(potential_content_divs):
                logger.info(f"#{i+1}: Class: {div_info['classes']}, Độ dài: {div_info['text_length']}, Mẫu: {div_info['sample']}")
                print(f"#{i+1}: Class: {div_info['classes']}, Độ dài: {div_info['text_length']}, Mẫu: {div_info['sample']}")
            
            # Check for shutdown before saving file
            if is_shutting_down:
                logger.warning("Shutdown requested, skipping file save")
                return
                
            # Lưu mã nguồn để phân tích thêm nếu cần
            logger.info("Lưu mã nguồn HTML vào file")
            try:
                with open('page_source.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.info("Đã lưu mã nguồn vào file page_source.html")
                print("\nĐã lưu mã nguồn vào file page_source.html")
            except Exception as e:
                logger.error(f"Lỗi khi lưu mã nguồn: {e}")
                print(f"Lỗi khi lưu mã nguồn: {e}")
    except Exception as e:
        logger.error(f"Error during structure check: {e}", exc_info=True)
    finally:
        total_time = time.time() - start_time
        logger.info(f"Kiểm tra cấu trúc trang web hoàn tất trong {total_time:.2f} giây")

async def run_with_graceful_shutdown():
    """Wrapper to handle graceful shutdown"""
    try:
        await check_structure()
    except asyncio.CancelledError:
        logger.warning("Task was cancelled")
    finally:
        logger.info("Structure check completed")

if __name__ == "__main__":
    try:
        logger.info("Starting web structure check")
        
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
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            except asyncio.CancelledError:
                pass
                
        finally:
            # Clean shutdown
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            
        logger.info("Web structure check completed successfully")
    except Exception as e:
        logger.critical(f"Lỗi không xử lý được: {e}", exc_info=True)
        print(f"Lỗi nghiêm trọng: {e}")
        sys.exit(1) 