"""Tests for the extractor module."""

import os
import unittest
from src.mtc_downloader.core.extractor import extract_chapter


class TestExtractor(unittest.TestCase):
    """Test cases for the extractor module."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_html_path = os.path.join(
            os.path.dirname(__file__), "data", "sample.html"
        )
        self.output_dir = os.path.join(
            os.path.dirname(__file__), "output"
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        """Clean up after tests."""
        for file in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)

    def test_extract_chapter(self):
        """Test extracting a single chapter from HTML file."""
        output_file = extract_chapter(self.sample_html_path, self.output_dir)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("Sample Story", content)
        self.assertIn("Chapter 1: The Beginning", content)
        self.assertIn("Đây là đoạn văn bản mẫu dùng để thử nghiệm", content)


if __name__ == "__main__":
    unittest.main() 