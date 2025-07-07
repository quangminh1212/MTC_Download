#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the downloader module
"""

import unittest
from unittest.mock import patch, MagicMock

from mtc_downloader.core.downloader import download_chapter


class TestDownloader(unittest.TestCase):
    """Test cases for the downloader module"""

    def test_download_chapter_invalid_url(self):
        """Test download_chapter with invalid URL"""
        result = download_chapter("https://example.com/invalid")
        self.assertIsNone(result)

    @patch('mtc_downloader.core.downloader.requests.get')
    def test_download_chapter_request_error(self, mock_get):
        """Test download_chapter with request error"""
        mock_get.return_value = MagicMock(status_code=404)
        result = download_chapter("https://metruyencv.com/truyen/test/chuong-1")
        self.assertIsNone(result)

    @patch('mtc_downloader.core.downloader.requests.get')
    @patch('mtc_downloader.core.downloader.BeautifulSoup')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_download_chapter_success(self, mock_open, mock_bs, mock_get):
        """Test download_chapter with success"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = "<html><body></body></html>"
        mock_get.return_value = mock_response

        # Mock BeautifulSoup
        mock_soup = MagicMock()
        mock_bs.return_value = mock_soup

        # Mock elements
        mock_chapter_title = MagicMock()
        mock_chapter_title.text = "Test Chapter"
        mock_soup.select_one.side_effect = [
            mock_chapter_title,  # chapter_title
            MagicMock(text="Test Story"),  # story_title
            MagicMock(get_text=lambda separator, strip: "Test content")  # story_content
        ]

        # Call function
        result = download_chapter("https://metruyencv.com/truyen/test/chuong-1", "test.txt")

        # Assertions
        self.assertEqual(result, "test.txt")
        mock_open.assert_called_once_with("test.txt", "w", encoding="utf-8")
        mock_open().write.assert_called_once()


if __name__ == '__main__':
    unittest.main() 