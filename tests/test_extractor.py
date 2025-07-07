"""Tests for the extractor module."""

import os
import unittest
from mtc_downloader.core.extractor import extract_story_content


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
        self.output_file = os.path.join(self.output_dir, "sample.txt")

    def tearDown(self):
        """Clean up after tests."""
        for file in os.listdir(self.output_dir):
            if file != ".gitkeep":  # Không xóa file .gitkeep
                file_path = os.path.join(self.output_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

    def test_extract_chapter(self):
        """Test extracting a single chapter from HTML file."""
        output_file = extract_story_content(self.sample_html_path, self.output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("Sample Story", content)
        self.assertIn("Chapter 1: The Beginning", content)
        self.assertIn("Đây là đoạn văn bản mẫu dùng để thử nghiệm", content)


if __name__ == "__main__":
    unittest.main() 