#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper.py – Web content scraper for tiemtruyenchu.com
Downloads readable (unencrypted) chapter text via authenticated sessions.
"""
import sys, io, re, time, json
from pathlib import Path
from typing import Optional, List, Dict

import requests
from bs4 import BeautifulSoup

SOURCE_BASE = "https://tiemtruyenchu.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
}
CONTENT_SELS = [
    ".chapter-content", "#chapter-c", "#content", ".chapter-c",
    ".box-chap", ".story-content", ".text-chapter", "article .content",
    "[id*='chapter']", ".chapter-text", "div.content",
]
TIMEOUT = 15


class Scraper:
    """Authenticated web scraper for tiemtruyenchu.com"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._logged_in = False

    # ── Auth ──────────────────────────────────────────────────────────────
    def login(self, username: str, password: str) -> bool:
        """Login via web form. Returns True on success."""
        try:
            # Get login page (CSRF token)
            resp = self.session.get(f"{SOURCE_BASE}/login", timeout=TIMEOUT)
            soup = BeautifulSoup(resp.text, "html.parser")
            csrf = None
            el   = soup.find("input", {"name": "_token"})
            if el:
                csrf = el.get("value")

            payload = {
                "username": username,
                "password": password,
                "_token":   csrf or "",
                "redirect": "/",
            }
            resp2 = self.session.post(
                f"{SOURCE_BASE}/login",
                data=payload,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            # If still on login page → failed
            if "Đăng nhập" in (resp2.text[:500]) and "form" in resp2.text[:2000]:
                return False
            self._logged_in = True
            return True
        except Exception as e:
            print(f"[scraper] login error: {e}", file=sys.stderr)
            return False

    def is_logged_in(self) -> bool:
        return self._logged_in

    # ── Book info ─────────────────────────────────────────────────────────
    def get_book_info(self, slug: str) -> Optional[Dict]:
        """Fetch book page and return basic info + chapter list."""
        url = f"{SOURCE_BASE}/truyen/{slug}"
        try:
            r = self.session.get(url, timeout=TIMEOUT)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            # Title
            title_el = (soup.find("h1") or soup.find("h2") or
                        soup.select_one(".title-story, .story-title"))
            title = title_el.get_text(strip=True) if title_el else slug

            # Chapter links
            ch_links = soup.select("a[href*='/chuong-']")
            chapters = []
            seen = set()
            for a in ch_links:
                href = a.get("href", "")
                if href in seen:
                    continue
                seen.add(href)
                m = re.search(r"/chuong-(\d+)", href)
                if m:
                    idx = int(m.group(1))
                    name = a.get_text(strip=True) or f"Chương {idx}"
                    chapters.append({
                        "index": idx,
                        "name":  name,
                        "url":   href if href.startswith("http")
                                 else SOURCE_BASE + href,
                    })
            chapters.sort(key=lambda c: c["index"])
            return {"title": title, "slug": slug, "chapters": chapters}
        except Exception as e:
            print(f"[scraper] book info error: {e}", file=sys.stderr)
            return None

    def get_chapter_urls(self, slug: str, total_hint: int = 0) -> List[Dict]:
        """Build chapter URL list. If book page doesn't list all, generate URLs."""
        info = self.get_book_info(slug)
        if info and info["chapters"]:
            return info["chapters"]
        # Fallback: generate URLs up to total_hint
        return [
            {"index": i, "name": f"Chương {i}",
             "url": f"{SOURCE_BASE}/truyen/{slug}/chuong-{i}"}
            for i in range(1, (total_hint or 10) + 1)
        ]

    # ── Chapter content ───────────────────────────────────────────────────
    def get_chapter_text(self, url: str, delay: float = 0.5) -> Optional[str]:
        """Fetch and extract plain text from a chapter URL."""
        time.sleep(delay)
        try:
            r = self.session.get(url, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                return None
            # Redirected to login page?
            if "Đăng nhập" in r.text[:800] and "/login" in r.url:
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            for sel in CONTENT_SELS:
                el = soup.select_one(sel)
                if el:
                    text = _clean_text(el)
                    if len(text) > 100:
                        return text
            # Last resort: largest text block
            texts = [_clean_text(d) for d in soup.find_all("div")
                     if len(d.get_text(strip=True)) > 200]
            return max(texts, key=len) if texts else None
        except Exception as e:
            print(f"[scraper] chapter error: {e}", file=sys.stderr)
            return None


# ── Text cleanup ──────────────────────────────────────────────────────────
def _clean_text(el) -> str:
    for tag in el.find_all(["script", "style", "nav", "header",
                             "footer", "aside", "ins", "iframe"]):
        tag.decompose()
    text = re.sub(r"<br\s*/?>", "\n", str(el), flags=re.IGNORECASE)
    text = re.sub(r"</?(p|div|section|h\d)[^>]*>", "\n", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    for ent, ch in [("&amp;","&"),("&lt;","<"),("&gt;",">"),
                    ("&quot;",'"'),("&#39;","'"),("&nbsp;"," ")]:
        text = text.replace(ent, ch)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# ── Quick CLI test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--user",  required=True)
    p.add_argument("--pass",  dest="pwd", required=True)
    p.add_argument("--slug",  default="lang-nhan-my-nu-moi-tu-van")
    p.add_argument("--ch",    type=int, default=1)
    args = p.parse_args()

    s = Scraper()
    print(f"Logging in as {args.user}...")
    ok = s.login(args.user, args.pwd)
    print(f"Login: {'OK' if ok else 'FAILED'}")
    if not ok:
        sys.exit(1)

    url = f"{SOURCE_BASE}/truyen/{args.slug}/chuong-{args.ch}"
    print(f"Fetching: {url}")
    text = s.get_chapter_text(url, delay=0)
    if text:
        print(f"Content ({len(text)} chars):\n")
        print(text[:1000])
    else:
        print("No content found (may need login or different slug)")
