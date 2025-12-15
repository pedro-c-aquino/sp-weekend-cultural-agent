from bs4 import BeautifulSoup
from datetime import datetime
from .calendar import TZ
from ..schemas import Event, Source


MONTHS_PT = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}


def parse_generic_listing(html: str, base_url: str) -> list[Event]:
    soup = BeautifulSoup(html, "html.parser")
    events: list[Event] = []
    for a in soup.select("a"):
        text = a.get_text(" ", strip=True)
        if not text:
            continue
        # naive heuristic: keep lines containing a date-like pattern
        if any(m in text.lower() for m in MONTHS_PT.keys()):
            events.append(
                Event(
                    title=text[:120],
                    starts_at=datetime.now(TZ),
                    link=a.get("href"),
                    source=Source(name="generic", url=base_url),
                )
            )
    return events
