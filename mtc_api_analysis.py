#!/usr/bin/env python3
"""
MTC API Analysis - Phân tích API từ MTC.apk
Base URLs tìm được:
- https://android.lonoapp.net/api
- https://api.lonoapp.net/api
- https://chat.truyen.onl/v1/rooms
- https://pub.truyen.onl/

Từ file translations, các chức năng chính:
- Đọc truyện (chapters)
- Tải truyện (download)
- Tìm kiếm (search)
- Thư viện cá nhân (library)
- Bình luận (comments)
- Đánh giá (reviews)
- Mở khóa chương (unlock)
"""

import requests
import json

class MTCApi:
    def __init__(self):
        self.base_url = "https://android.lonoapp.net/api"
        self.api_url = "https://api.lonoapp.net/api"
        self.headers = {
            "User-Agent": "MTC/Android",
            "Content-Type": "application/json"
        }

    def test_endpoints(self):
        """Test các endpoint có thể có"""
        endpoints = [
            "/chapters",
            "/chapters?filter",
            "/books",
            "/stories",
            "/search",
            "/categories",
            "/genres",
            "/popular",
            "/latest",
            "/recommended"
        ]

        print("Testing endpoints...")
        for endpoint in endpoints:
            url = self.base_url + endpoint
            try:
                response = requests.get(url, headers=self.headers, timeout=5)
                print(f"[{response.status_code}] {url}")
                if response.status_code == 200:
                    print(f"  Response: {response.text[:200]}")
            except Exception as e:
                print(f"[ERROR] {url}: {e}")

    def get_chapters(self, book_id, page=1, limit=100):
        """Lấy danh sách chương của truyện"""
        url = f"{self.base_url}/chapters"
        params = {
            "book_id": book_id,
            "page": page,
            "limit": limit
        }
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error getting chapters: {e}")
            return None

    def download_chapter(self, chapter_id):
        """Tải nội dung chương"""
        url = f"{self.base_url}/chapters/{chapter_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error downloading chapter: {e}")
            return None

if __name__ == "__main__":
    api = MTCApi()
    print("=== MTC API Analysis ===")
    print(f"Base URL: {api.base_url}")
    print(f"API URL: {api.api_url}")
    print("\nTesting endpoints...")
    api.test_endpoints()
