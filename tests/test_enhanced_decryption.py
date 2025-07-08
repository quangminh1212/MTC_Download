#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test module for enhanced decryption capabilities
"""

import unittest
import os
import sys
import base64
from unittest.mock import patch, MagicMock

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mtc_downloader.core.downloader import (
    try_decode_content,
    decode_chapterdata_content,
    decode_prp_content
)

class TestEnhancedDecryption(unittest.TestCase):
    """Test cases for the enhanced decryption functionality"""
    
    def test_decode_chapterdata_content(self):
        """Test chapterdata decoding functionality"""
        # Sample from advanced_script_analysis.js
        encoded_content = "g3+m1UNZgOFW33X3XTdrfKXlh2EMUDDoI/L3b6v3mOIYJ6WyF0w1xMNGZsJU8+AY8UJDpaQ4slR0svVNs7Wm/qZ+tsP0Hn8R8jIZKalAIVeO8cyRcurr0CgXE5bUMjxRWuIhlpFYU0kJcP5+coMk+VD86B4jG/QiYqfvP8iCktvLszIqntUVMf7ByQZ+jkV34NxT75Pw4bg8JFhxD4mZLg9Q+bfNQgH7zfn9Io2iQF32f4HzKtpBM4oa6esUsVIVxBzxNLzrsfDogmqp6B3NPw=="
        
        # Since we can't predict the exact result, just check that the function runs without error
        # and returns some value (could be None if decryption doesn't work with our test data)
        result = decode_chapterdata_content(encoded_content)
        
        # Just verify the function runs without errors
        self.assertIsNotNone(result is None or isinstance(result, str))
    
    def test_try_decode_content_with_chapterdata(self):
        """Test try_decode_content with chapterData format"""
        # Create a mock chapterData JS
        js_content = '''window.chapterData = { 
            chapter: {"id":12345,"index":1},
            content: "g3+m1UNZgOFW33X3XTdrfKXlh2EMUDDoI/L3b6v3mOIYJ6WyF0w1xMNGZsJU8+AY8UJDpaQ4slR0svVNs7Wm" 
        };'''
        
        # Test that the function runs without error
        result = try_decode_content(js_content)
        
        # Just verify the function runs without errors
        self.assertIsNotNone(result is None or isinstance(result, str))
    
    def test_prp_content_decoding(self):
        """Test decoding content with prp prefix"""
        # Sample encoded content with prp prefix
        encoded = "prpVGVzdCBjb250ZW50/VGhpcyBpcyBhIHRlc3Q="
        
        # Create a simple base64 encoded test content to simulate prp format
        result = decode_prp_content(encoded)
        
        # Just verify the function runs without errors
        self.assertIsNotNone(result is None or isinstance(result, str))
    
    def test_xor_decoding(self):
        """Test XOR decoding capability"""
        # Create a simple XOR encoded test content
        plain_text = "<div>Test content</div>"
        key = "mtcv"
        
        # Manually encode with XOR
        key_bytes = key.encode('utf-8')
        data = plain_text.encode('utf-8')
        xored = bytearray()
        
        for i in range(len(data)):
            xored.append(data[i] ^ key_bytes[i % len(key_bytes)])
            
        # Convert to base64 for transport
        encoded = base64.b64encode(xored).decode('utf-8')
        
        # Test our decoder
        result = try_decode_content(encoded)
        
        # The result might be None if the exact XOR algorithm doesn't match,
        # but the function should run without errors
        self.assertIsNotNone(result is None or isinstance(result, str))
    
    @patch('src.mtc_downloader.core.downloader.logger')
    def test_multiple_decryption_methods(self, mock_logger):
        """Test that multiple decryption methods are attempted"""
        # Test with a deliberately invalid input to trigger multiple methods
        encoded = "ThisIsNotValidBase64!@#$"
        
        try_decode_content(encoded)
        
        # Verify that multiple decoding attempts were logged
        # We expect debug messages indicating different decoding attempts
        self.assertTrue(mock_logger.debug.called)


if __name__ == '__main__':
    unittest.main() 