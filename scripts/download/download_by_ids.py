#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Download by IDs - DISABLED
Only use download_one_completed_book.py for exactly one completed story per run.
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def main():
    print('DISABLED: download_by_ids.py has been disabled.')
    print('Use: python download_one_completed_book.py --book-id <ID_COMPLETED>')
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
