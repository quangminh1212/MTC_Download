#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import re

# Test decode một đoạn text
test_text = r"Truy\u1ec7n Pokemon th\u01b0\u1eddng ng\u00e0y"

print("Original:", test_text)

# Thử decode
try:
    decoded = codecs.decode(test_text, 'unicode_escape')
    print("Decoded:", decoded)
except Exception as e:
    print("Error:", e)

# Thử với regex
def decode_unicode_match(match):
    try:
        return codecs.decode(match.group(0), 'unicode_escape')
    except:
        return match.group(0)

decoded_regex = re.sub(r'\\u[0-9a-fA-F]{4}', decode_unicode_match, test_text)
print("Regex decoded:", decoded_regex)
