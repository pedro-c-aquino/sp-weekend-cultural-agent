import httpx, asyncio, time
from pathlib import Path


HEADERS = {"User-Agent": "sp-agent/0.1 (+github)"}


async def fetch(url: str, timeout=20) -> str:
    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=timeout
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
