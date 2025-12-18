# file: actor/scraper.py

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone

import aiohttp

from spagent.utils import html_to_text


DEFAULT_HEADERS = {
    "User-Agent": "sp-weekend-bot/1.0 (+https://github.com/pedro-c-aquino/sp-weekend-cultural-agent)"
}


async def fetch(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 15,
) -> Optional[str]:
    try:
        async with session.get(url, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None


async def fetch_all(
    urls: List[str],
    concurrency: int = 6,
    delay: float = 0.15,
) -> List[Dict]:
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:

        async def _fetch_one(url: str):
            async with semaphore:
                raw_html = await fetch(session, url)
                await asyncio.sleep(delay)
                if raw_html is None:
                    return {
                        "url": url,
                        "ok": False,
                        "text": None,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }

                clean_text = html_to_text(raw_html)
                return {
                    "url": url,
                    "text": clean_text,
                    "ok": True,
                    "html_len": len(raw_html),
                    "text_len": len(clean_text),
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }

        tasks = [_fetch_one(u) for u in urls]
        for coro in asyncio.as_completed(tasks):
            try:
                results.append(await coro)
            except Exception:
                continue

    return results


async def scrape_pages(
    urls: List[str],
    concurrency: int = 6,
    delay: float = 0.15,
) -> List[Dict]:
    """
    Fetch pages and return raw HTML.
    No parsing. No extraction.
    """
    return await fetch_all(urls, concurrency=concurrency, delay=delay)
