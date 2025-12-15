# file: actor/scraper.py
import asyncio
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from datetime import datetime, timezone
import json

# simple price regex (Brazilian common formats)
PRICE_RE = re.compile(r"(R\$\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)", re.I)
CURRENCY_MAP = {"R$": "BRL", "USD": "USD", "EUR": "EUR"}

DEFAULT_HEADERS = {
    "User-Agent": "sp-weekend-bot/1.0 (+https://github.com/pedro-c-aquino/sp-weekend-cultural-agent)"
}


async def fetch(
    session: aiohttp.ClientSession, url: str, timeout: int = 15
) -> Optional[str]:
    try:
        async with session.get(url, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None


def extract_json_ld(soup: BeautifulSoup) -> List[dict]:
    out = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            raw = tag.string
            if not raw:
                continue
            parsed = json.loads(raw)
            # parsed can be a list or an object
            if isinstance(parsed, list):
                out.extend(parsed)
            else:
                out.append(parsed)
        except Exception:
            # Some sites wrap multiple JSON objects without valid JSON — try naive fixes
            text = tag.string or ""
            # attempt to split objects heuristically
            for chunk in re.split(r"\}\s*\{", text):
                try:
                    maybe = chunk.strip()
                    if not maybe:
                        continue
                    if not maybe.startswith("{"):
                        maybe = "{" + maybe
                    if not maybe.endswith("}"):
                        maybe = maybe + "}"
                    out.append(json.loads(maybe))
                except Exception:
                    continue
    return out


def parse_price(text: str) -> Optional[str]:
    if not text:
        return None
    m = PRICE_RE.findall(text)
    if m:
        return " – ".join(sorted(set(m), key=lambda s: text.find(s)))
    return None


def parse_date_from_text(candidate: str) -> Optional[str]:
    if not candidate:
        return None
    # normalize a bit of Portuguese words that may confuse parser
    try:
        # remove 'às' or 'as' noise, keep hour info
        cleaned = candidate.replace("às", " ").replace("as ", " ")
        dt = dateparser.parse(cleaned, dayfirst=True, fuzzy=True)
        if dt:
            # return ISO format in local time (no tz conversion)
            return dt.isoformat()
    except Exception:
        return None
    return None


def extract_from_json_ld_block(obj: dict) -> List[dict]:
    events = []
    typ = obj.get("@type") or obj.get("type")
    if typ:
        if isinstance(typ, list):
            is_event = any("Event" in t or t.lower() == "event" for t in typ)
        else:
            is_event = "Event" in typ or typ.lower() == "event"
    else:
        is_event = False

    if is_event:
        e = {}
        e["title"] = obj.get("name")
        e["start"] = obj.get("startDate")
        e["end"] = obj.get("endDate")
        e["date_text"] = (
            obj.get("startDate") or obj.get("date") or obj.get("description")
        )
        # price
        offers = obj.get("offers")
        if isinstance(offers, dict):
            price_text = (
                offers.get("price")
                or offers.get("priceSpecification")
                or offers.get("priceCurrency")
            )
            if price_text and isinstance(price_text, (int, float, str)):
                e["price"] = str(price_text)
                e["currency"] = offers.get("priceCurrency")
        elif isinstance(offers, list) and offers:
            # combine
            ps = []
            for o in offers:
                if isinstance(o, dict):
                    if "price" in o:
                        p = o.get("price")
                        if p:
                            ps.append(str(p))
            if ps:
                e["price"] = " – ".join(ps)
        # location
        loc = obj.get("location")
        if isinstance(loc, dict):
            e["location"] = loc.get("name") or " ".join(
                filter(
                    None,
                    [
                        loc.get("address", {}).get("streetAddress", ""),
                        loc.get("address", {}).get("addressLocality", ""),
                    ],
                )
            )
        elif isinstance(loc, str):
            e["location"] = loc
        e["raw"] = obj
        events.append(e)
    return events


def fallback_extract_from_html(soup: BeautifulSoup, url: str) -> List[dict]:
    """
    Heuristics for common ticketing/city-guide pages.
    """
    out = []
    # Candidate title selectors
    title = None
    for sel in [
        "h1",
        ".event-title",
        ".entry-title",
        ".title",
        "meta[property='og:title']",
    ]:
        el = soup.select_one(sel)
        if el:
            if sel.startswith("meta"):
                title = el.get("content")
            else:
                title = el.get_text(strip=True)
            if title:
                break

    # candidate date selectors
    date_text = None
    for sel in [
        ".date",
        ".event-date",
        ".datatime",
        ".when",
        ".event-time",
        ".event-dates",
        ".show-date",
        ".card-date",
    ]:
        el = soup.select_one(sel)
        if el:
            date_text = el.get_text(" ", strip=True)
            break

    # price
    price_text = None
    for sel in [".price", ".ticket-price", ".valor", ".preco", ".price-range"]:
        el = soup.select_one(sel)
        if el:
            price_text = el.get_text(" ", strip=True)
            break

    # try to gather multiple event cards on page
    # look for event list items
    cards = soup.select(".event, .evento, .card-event, .search-result, .event-item")
    if cards:
        for c in cards:
            t = None
            d = None
            p = None
            # title
            for s in ["h2", "h3", ".title", ".event-name", ".card-title", ".name"]:
                el = c.select_one(s)
                if el:
                    t = el.get_text(" ", strip=True)
                    break
            # date
            for s in [".date", ".when", ".event-date", ".meta-date"]:
                el = c.select_one(s)
                if el:
                    d = el.get_text(" ", strip=True)
                    break
            # price
            for s in [".price", ".valor", ".preco", ".ticket-price"]:
                el = c.select_one(s)
                if el:
                    p = el.get_text(" ", strip=True)
                    break
            if t:
                out.append(
                    {
                        "title": t,
                        "date_text": d,
                        "price": parse_price(p or (c.get_text(" ", strip=True))),
                        "location": None,
                        "url": url,
                        "raw": None,
                    }
                )
        return out

    # fallback single-event page
    if title:
        out.append(
            {
                "title": title,
                "date_text": date_text,
                "price": parse_price(price_text or (soup.get_text(" ", strip=True))),
                "location": None,
                "url": url,
                "raw": None,
            }
        )
    return out


async def scrape_pages(
    urls: List[str], concurrency: int = 6, delay: float = 0.2
) -> List[dict]:
    """Fetch pages and extract event dicts."""
    sem = asyncio.Semaphore(concurrency)
    results = []

    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:

        async def worker(u):
            async with sem:
                html = await fetch(session, u)
                if not html:
                    return
                soup = BeautifulSoup(html, "html.parser")

                # Try JSON-LD first
                json_blocks = extract_json_ld(soup)
                items = []
                if json_blocks:
                    for b in json_blocks:
                        items.extend(extract_from_json_ld_block(b))

                # Fallback heuristics
                if not items:
                    items = fallback_extract_from_html(soup, u)

                # Normalize each item
                for it in items:
                    title = it.get("title") or ""
                    date_text = it.get("date_text") or it.get("date") or ""
                    deduced_start = it.get("start") or parse_date_from_text(date_text)
                    price = it.get("price") or parse_price(
                        it.get("price") or date_text or ""
                    )
                    currency = None
                    if price:
                        for token, cur in CURRENCY_MAP.items():
                            if token in price:
                                currency = cur
                                break

                    results.append(
                        {
                            "title": title,
                            "start": deduced_start,
                            "end": it.get("end"),
                            "date_text": date_text,
                            "price": price,
                            "currency": currency,
                            "location": it.get("location"),
                            "url": u,
                            "source": urlparse(u).netloc,
                            "raw_extracted": it.get("raw") or None,
                        }
                    )
                # polite delay
                await asyncio.sleep(delay)

        await asyncio.gather(*[worker(u) for u in urls])

    # dedupe by title + start + url
    seen = set()
    deduped = []
    for r in results:
        key = (
            (r.get("title") or "")[:200]
            + "|"
            + str(r.get("start"))
            + "|"
            + (r.get("url") or "")
        )
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped
