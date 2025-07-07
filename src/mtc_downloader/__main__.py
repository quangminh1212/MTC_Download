#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Điểm vào chính của ứng dụng khi chạy từ module
"""

import sys
from mtc_downloader.cli import download_cmd

if __name__ == "__main__":
    # Mặc định chạy lệnh download
    download_cmd() 