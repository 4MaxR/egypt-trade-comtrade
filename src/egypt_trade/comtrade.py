"""Minimal UN Comtrade client.

Without a key it uses the public preview endpoint (one period per call, 500 rows max,
roughly one request per second). Set COMTRADE_API_KEY to use the keyed data endpoint,
which lifts the row cap to 100,000. Both return the same record shape.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

PREVIEW_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
DATA_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
REFERENCE_URL = "https://comtradeapi.un.org/files/v1/app/reference/{name}.json"

PREVIEW_ROW_CAP = 500
MIN_INTERVAL_S = 1.2


class ComtradeError(RuntimeError):
    pass


class Client:
    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("COMTRADE_API_KEY")
        self.timeout = timeout
        self._last_call = 0.0

    @property
    def row_cap(self) -> int | None:
        return None if self.api_key else PREVIEW_ROW_CAP

    def _request(self, url: str, headers: dict[str, str] | None = None) -> dict:
        for attempt in range(6):
            wait = MIN_INTERVAL_S - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            req = urllib.request.Request(url, headers=headers or {})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504):
                    time.sleep(2 * (attempt + 1))
                    continue
                raise ComtradeError(f"HTTP {exc.code} for {url}: {exc.read()[:300]!r}") from exc
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 * (attempt + 1))
        raise ComtradeError(f"Gave up after repeated failures: {url}")

    def get(self, period: int, **params: str) -> list[dict]:
        """Fetch one annual period. Raises if the response may have been truncated."""
        query = {"period": str(period), **params}
        headers = {}
        if self.api_key:
            base = DATA_URL
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        else:
            base = PREVIEW_URL
        payload = self._request(f"{base}?{urllib.parse.urlencode(query)}", headers)
        if payload.get("error"):
            raise ComtradeError(f"{payload['error']} ({query})")
        rows = payload.get("data") or []
        if self.row_cap and len(rows) >= self.row_cap:
            raise ComtradeError(
                f"{len(rows)} rows hit the preview cap for {query}; "
                "split the query or set COMTRADE_API_KEY"
            )
        return rows

    def reference(self, name: str) -> list[dict]:
        payload = self._request(REFERENCE_URL.format(name=name))
        return payload["results"]
