#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

# Test nhiều URL chương
test_urls = [
    'https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong/chuong-1',
    'https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong/chuong-2',
    'https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong/chuong-3'
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

for url in test_urls:
    try:
        print(f'\nTesting: {url}')
        response = requests.get(url, headers=headers, timeout=10)
        print(f'Status: {response.status_code}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            print(f'Title: {title.text if title else "No title"}')

            # Kiểm tra có script chứa chapterData không
            scripts = soup.find_all('script')
            found_data = False
            for script in scripts:
                if script.string and 'chapterData' in script.string:
                    print('✓ Tìm thấy chapterData trong script')
                    found_data = True
                    break

            if not found_data:
                print('✗ Không tìm thấy chapterData')

        else:
            print(f'✗ Lỗi HTTP: {response.status_code}')

    except Exception as e:
        print(f'✗ Lỗi: {e}')
