"""conftest.py – pytest root path setup.

Ensures ``mtc`` package is importable when running tests via ``pytest tests/``.
"""
import sys
from pathlib import Path

# Add project root to sys.path so all tests can import mtc.* without
# manual sys.path manipulation in each test file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
