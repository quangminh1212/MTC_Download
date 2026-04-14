"""Smoke tests for mtc.api and mtc.downloader modules."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mtc.api import create_session, search_books, fetch_full_catalog, resolve_book
from mtc.downloader import load_catalog
from mtc.utils import safe_name


def test_safe_name():
    assert safe_name('Hello / World: "test"') == "Hello _ World_ _test_"
    assert safe_name("Chương 1") == "Chương 1"
    print("✔ safe_name")


def test_create_session():
    s = create_session()
    assert s.headers.get("x-app") == "app.android"
    print("✔ create_session")


def test_load_catalog():
    books = load_catalog()
    assert isinstance(books, list)
    if books:
        assert "id" in books[0]
        assert "name" in books[0]
    print(f"✔ load_catalog ({len(books)} books)")


def test_search(keyword="Hồn Đế"):
    s = create_session()
    results = search_books(s, keyword)
    assert isinstance(results, list)
    print(f"✔ search '{keyword}' -> {len(results)} results")
    for b in results[:3]:
        print(f"  #{b['id']} {b['name']}")


def test_resolve():
    s = create_session()
    book = resolve_book(s, "Vạn Biến Hồn Đế")
    assert book is not None
    assert book.get("id")
    print(f"✔ resolve -> #{book['id']} {book['name']}")


if __name__ == "__main__":
    test_safe_name()
    test_create_session()
    test_load_catalog()
    test_search()
    test_resolve()
    print("\nAll tests passed!")
