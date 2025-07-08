#!/usr/bin/env python3
"""
Test script để kiểm tra các sửa đổi trong main.py
"""

import asyncio
from playwright.async_api import async_playwright

async def test_login_selectors():
    """Test các selector mới cho login"""
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)  # Hiển thị browser để debug
        page = await browser.new_page()
        
        try:
            print("Đang truy cập metruyencv.com...")
            await page.goto('https://metruyencv.com/', timeout=30000)
            
            # Test login button selectors
            login_selectors = [
                'xpath=/html/body/div[1]/header/div/div/div[3]/button',
                'button:has-text("Đăng nhập")',
                'button[class*="login"]',
                'a[href*="login"]'
            ]
            
            print("Đang tìm nút đăng nhập...")
            login_found = False
            for i, selector in enumerate(login_selectors):
                try:
                    element = await page.locator(selector).first
                    if await element.is_visible():
                        print(f"✅ Tìm thấy nút đăng nhập với selector {i+1}: {selector}")
                        login_found = True
                        break
                except:
                    print(f"❌ Không tìm thấy với selector {i+1}: {selector}")
            
            if not login_found:
                print("❌ Không tìm thấy nút đăng nhập nào")
                # Thử tìm tất cả button để debug
                buttons = await page.query_selector_all('button')
                print(f"Tìm thấy {len(buttons)} button trên trang")
                for i, btn in enumerate(buttons[:5]):  # Chỉ hiển thị 5 button đầu
                    text = await btn.inner_text()
                    print(f"Button {i+1}: '{text}'")
            
            await asyncio.sleep(3)  # Để có thể quan sát
            
        except Exception as e:
            print(f"Lỗi: {e}")
        finally:
            await browser.close()

async def test_chapter_content_selectors():
    """Test các selector cho chapter content"""
    test_url = "https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong/chuong-1"
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print(f"Đang truy cập chapter test: {test_url}")
            await page.goto(test_url, timeout=30000)
            
            # Test content selectors
            content_selectors = [
                '#chapter-content',
                '[class*="chapter-content"]',
                '[class*="content"]',
                'main [class*="text"]'
            ]
            
            print("Đang tìm nội dung chapter...")
            content_found = False
            for i, selector in enumerate(content_selectors):
                try:
                    element = await page.locator(selector).first
                    if await element.is_visible():
                        text = await element.inner_text()
                        if len(text.strip()) > 100:
                            print(f"✅ Tìm thấy nội dung với selector {i+1}: {selector}")
                            print(f"   Độ dài nội dung: {len(text)} ký tự")
                            print(f"   Nội dung đầu: {text[:100]}...")
                            content_found = True
                            break
                except Exception as e:
                    print(f"❌ Lỗi với selector {i+1}: {selector} - {e}")
            
            if not content_found:
                print("❌ Không tìm thấy nội dung chapter")
            
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"Lỗi: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    print("=== Test Login Selectors ===")
    asyncio.run(test_login_selectors())
    
    print("\n=== Test Chapter Content Selectors ===")
    asyncio.run(test_chapter_content_selectors())
    
    print("\n=== Test hoàn thành ===")
