import httpx

from spagent.utils import dedupe_serp, serp_score
from ..tools.web_search import WebSearch
from ..tools.fetch import fetch
from ..tools.parse import parse_generic_listing
import asyncio


class Actor:
    def __init__(self):
        self.search = WebSearch()

    def websearch(self, q: str, k: int = 12, timelimit: str | None = "w"):
        raw = self.search.search(q, max_results=k, timelimit=timelimit)
        ranked = sorted(raw, key=lambda r: serp_score(r), reverse=True)
        return dedupe_serp(ranked)

    async def crawl(self, urls: list[str]) -> list[tuple[str, str]]:
        await self._ensure_client()
        htmls = await asyncio.gather(*(fetch(u, client=self._client) for u in urls))
        return [(u, h) for u, h in zip(urls, htmls) if h]

    async def aclose(self):
        if self._client:
            await self._client.aclose()
            self._client = None
