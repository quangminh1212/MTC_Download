#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="mtc_downloader",
    version="1.0.0",
    description="Công cụ tải và trích xuất nội dung truyện từ MetruyenCV",
    author="MTC Downloader Team",
    author_email="example@example.com",
    url="https://github.com/example/mtc_downloader",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "requests>=2.23.0",
        "flask>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mtc-download=mtc_downloader.cli:download_cmd",
            "mtc-extract=mtc_downloader.cli:extract_cmd",
            "mtc-web=mtc_downloader.cli:web_cmd",
            "mtc-gui=mtc_downloader.cli:gui_cmd",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.6",
) 