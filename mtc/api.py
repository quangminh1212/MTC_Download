"""api.py – MTC book listing API client."""
from typing import Optional, Dict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import API_BASE, USER_AGENT, API_TIMEOUT, API_RETRY

# Book status constants
STATUS_ALL       = 0
STATUS_ONGOING   = 1
STATUS_COMPLETED = 2
STATUS_PAUSED    = 3


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


def search_books(session: requests.Session, query: str,
                 page: int = 1, status: int = STATUS_ALL) -> Dict:
    params = {"search": query, "per_page": 50, "page": page}
    if status:
        params["filter[status]"] = status
    return _get(session, "books", params)


def list_books(session: requests.Session, page: int = 1, per_page: int = 50,
               status: int = STATUS_COMPLETED) -> Dict:
    """List books. Default: only completed (status=2)."""
    params = {"per_page": per_page, "page": page}
    if status:
        params["filter[status]"] = status
    return _get(session, "books", params)

