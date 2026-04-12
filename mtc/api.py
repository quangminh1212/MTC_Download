"""api.py – MTC book listing API client."""
from typing import Optional, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import API_BASE, USER_AGENT, API_TIMEOUT, API_RETRY


def make_session(token: Optional[str] = None) -> requests.Session:
    """Create HTTP session with retry."""
    s = requests.Session()
    retry = Retry(total=API_RETRY, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


def _get(session: requests.Session, path: str, params: dict = None) -> Dict:
    resp = session.get(f"{API_BASE}/{path}", params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def search_books(session: requests.Session, query: str, page: int = 1) -> Dict:
    return _get(session, "books", {"search": query, "per_page": 20, "page": page})


def list_books(session: requests.Session, page: int = 1, per_page: int = 20) -> Dict:
    return _get(session, "books", {"per_page": per_page, "page": page})
