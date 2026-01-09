from typing import List

from spagent.chains.extractor import ExtractorChain
from spagent.tools.fetchers import fetch_sao_paulo_secreto_fetcher, fetch_sympla_fetcher
from ..schemas import Event, FetchResult

extractor = ExtractorChain(model="phi3:mini")


async def fetch_sympla() -> FetchResult:
    return await fetch_sympla_fetcher()


async def fetch_sao_paulo_secreto() -> FetchResult:
    return await fetch_sao_paulo_secreto_fetcher()


async def extract_events(page: FetchResult) -> List[Event]:
    return await extractor.extract(page)


async def dedupe_events(events: List[Event] = None) -> List[Event]:
    return events or []


async def validate_events(events: List[Event] = None) -> List[Event]:
    return events or []


async def websearch_events() -> List[Event]:
    return []


TOOLS = {
    "fetch_sympla": fetch_sympla,
    "fetch_sao_paulo_secreto": fetch_sao_paulo_secreto,
    "extract_events": extract_events,
    "dedupe_events": dedupe_events,
    "validate_events": validate_events,
    "websearch_events": websearch_events,
}
