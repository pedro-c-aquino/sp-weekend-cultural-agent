from typing import List
from ..schemas import Event


async def crawl_sympla() -> List[Event]:
    return []


async def crawl_sao_paulo_secreto() -> List[Event]:
    return []


async def dedupe_events(events: List[Event] = None) -> List[Event]:
    return events or []


async def validate_events(events: List[Event] = None) -> List[Event]:
    return events or []


async def websearch_events() -> List[Event]:
    return []


TOOLS = {
    "crawl_sympla": crawl_sympla,
    "crawl_sao_paulo_secreto": crawl_sao_paulo_secreto,
    "dedupe_events": dedupe_events,
    "validate_events": validate_events,
    "websearch_events": websearch_events,
}
