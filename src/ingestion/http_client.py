from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import HTTP_TIMEOUT, REQUEST_DELAY_SECONDS, USER_AGENT

log = logging.getLogger(__name__)


class PoliteClient:
    """Wraps requests with rate limiting, retries, and a recognisable UA."""

    def __init__(self, delay: float = REQUEST_DELAY_SECONDS, headers: dict[str, str] | None = None):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        if headers:
            self.session.headers.update(headers)
        self._last_call: float = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_call = time.monotonic()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
    def get(self, url: str, **kwargs: Any) -> Response:
        self._throttle()
        resp = self.session.get(url, timeout=HTTP_TIMEOUT, **kwargs)
        if resp.status_code in (429, 503):
            log.warning("rate limit hit: %s -> %s", url, resp.status_code)
            resp.raise_for_status()
        resp.raise_for_status()
        return resp
