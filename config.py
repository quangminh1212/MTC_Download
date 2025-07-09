#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cấu hình cho MeTruyenCV Downloader
"""

# Cấu hình chung
DEFAULT_DELAY = 1  # Thời gian nghỉ giữa các lần tải (giây)
TIMEOUT = 10  # Timeout cho WebDriverWait (giây)
HEADLESS = True  # Chạy browser ở chế độ headless

# Cấu hình thư mục
OUTPUT_DIR = "truyen"  # Thư mục lưu truyện

# Cấu hình XPath selectors
XPATH_SELECTORS = {
    "story_title": [
        "//h1[contains(@class, 'title')]",
        "//h1[contains(@class, 'story-title')]",
        "//h1[@class='title']",
        "//h1"
    ],
    "author": [
        "//a[contains(@href, '/tac-gia/')]",
        "//span[contains(@class, 'author')]"
    ],
    "chapter_list": [
        "//a[contains(@href, '/chuong-')]",
        "//a[contains(@href, 'chuong')]"
    ],
    "chapter_content": [
        "//div[@id='chapter-content']",
        "//div[contains(@class, 'chapter-content')]",
        "//div[contains(@class, 'content')]",
        "//div[contains(@class, 'story-content')]",
        "//div[@class='content']"
    ],
    "muc_luc_button": [
        "//a[contains(text(), 'Mục Lục')]",
        "//a[contains(text(), 'Danh sách chương')]",
        "//button[contains(text(), 'Mục Lục')]"
    ]
}

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Cấu hình Chrome options
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-blink-features=AutomationControlled",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images"  # Tắt tải hình ảnh để tăng tốc
]
