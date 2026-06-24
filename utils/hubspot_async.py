# =============================================================
# utils/hubspot_async.py — Client HTTP HubSpot ASYNC
# =============================================================
# Semaphore(5) : jamais plus de 5 requêtes simultanées
# Retry automatique sur HTTP 429 avec respect du Retry-After
# =============================================================

import asyncio
import re
import httpx
from config import HUBSPOT_ACCESS_TOKEN

BASE_URL = "https://api.hubapi.com"

_HUBSPOT_SEMAPHORE = asyncio.Semaphore(5)

def _check_credentials():
    if not HUBSPOT_ACCESS_TOKEN:
        raise RuntimeError("HUBSPOT_ACCESS_TOKEN non configuré.")

def _async_headers() -> dict:
    _check_credentials()
    return {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

def _parse_retry_after(response: httpx.Response, default_seconds: float = 2.0) -> float:
    ra = response.headers.get("Retry-After")
    if ra:
        try:
            return float(ra)
        except (ValueError, TypeError):
            pass
    try:
        body = response.json()
        msg = body.get("message", "") or ""
        m = re.search(r"(\d+)\s+second", msg, re.IGNORECASE)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return default_seconds

async def hubspot_get_async(
    path: str,
    params: dict = None,
    timeout: float = 20.0,
) -> dict:
    """
    GET HubSpot async avec protection rate limit.
    Retry x3 sur HTTP 429, backoff progressif.
    """
    _check_credentials()
    url = BASE_URL + path
    headers = _async_headers()

    async with _HUBSPOT_SEMAPHORE:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        ) as client:
            max_attempts = 3
            for attempt in range(max_attempts):
                r = await client.get(url, headers=headers, params=params or {})

                if r.status_code == 429:
                    if attempt < max_attempts - 1:
                        wait = _parse_retry_after(r, default_seconds=2.0 * (attempt + 1))
                        await asyncio.sleep(wait)
                        continue
                    else:
                        raise RuntimeError(
                            f"GET {path} → HTTP 429 après {max_attempts} tentatives."
                        )

                if r.is_success:
                    return r.json()

                raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")

    raise RuntimeError(f"GET {path} → échec inattendu.")