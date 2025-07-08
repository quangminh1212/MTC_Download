#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import requests
from bs4 import BeautifulSoup
from mtc_downloader.core.downloader import download_chapter

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_trending_novel_urls():
    """Tìm các URL chương truyện đang hot trên trang chủ"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }
        
        response = requests.get("https://metruyencv.com", headers=headers)
        if response.status_code != 200:
            print(f"Không thể truy cập trang chủ: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm các liên kết đến truyện
        story_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/truyen/' in href and 'chuong' not in href:
                story_links.append(href)
        
        # Lấy URL của 3 truyện đầu tiên
        novel_urls = []
        for i, link in enumerate(story_links[:3]):
            if not link.startswith('http'):
                link = f"https://metruyencv.com{link}"
            
            # Thêm /chuong-1 vào cuối URL
            chapter_url = f"{link.rstrip('/')}/chuong-1"
            novel_urls.append(chapter_url)
            
        return novel_urls
    except Exception as e:
        print(f"Lỗi khi tìm URL truyện: {str(e)}")
        return []

def main():
    # Thử các URL từ các định dạng khác nhau
    urls = [
        'https://metruyencv.com/truyen/dai-quoc-cong-nuong/chuong-1',
        'https://metruyencv.com/doc-truyen/dai-quoc-cong-nuong/chuong-1'
    ]
    
    # Thêm các URL từ trang chủ hiện tại
    trending_urls = get_trending_novel_urls()
    if trending_urls:
        print(f"Đã tìm thấy {len(trending_urls)} URL truyện đang hot:")
        for url in trending_urls:
            print(f"  - {url}")
        urls.extend(trending_urls)
    
    for i, url in enumerate(urls):
        print(f"\n{'='*50}\nThử URL #{i+1}: {url}\n{'='*50}")
        output_file = f"test_output_{i+1}.txt"
        result = download_chapter(url, output_file)
        if result:
            print(f"Tải thành công: {result}")
        else:
            print(f"Tải thất bại URL: {url}")
    
    print("\nHoàn tất kiểm tra!")

if __name__ == "__main__":
    main() 