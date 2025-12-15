import re
from urllib.parse import urlparse

PT_WEEKEND = r"(sexta|sexta-feira|sábado|sabado|domingo|fim de semana|final de semana|hoje|amanh[ãa])"
PT_SP = r"(s[aã]o paulo|sao paulo|sp\\b)"
PT_INTENT = (
    r"(samba|show|teatro|pe[cç]a|exposi[cç][aã]o|evento|agenda|programa[cç][aã]o)"
)


def serp_score(item: dict, focus: str = "samba") -> float:
    title = (item.get("title") or "").lower()
    body = (item.get("body") or "").lower()
    url = (item.get("href") or item.get("url") or "").lower()

    weekend = (
        1.0 if (re.search(PT_WEEKEND, title) or re.search(PT_WEEKEND, body)) else 0.0
    )
    sp = 1.0 if (re.search(PT_SP, title) or re.search(PT_SP, body)) else 0.0
    intent = (
        1.0
        if (
            re.search(PT_INTENT, title)
            or re.search(PT_INTENT, body)
            or focus.lower() in title
            or focus.lower() in body
        )
        else 0.0
    )

    # prefer well-known domains slightly
    host = urlparse(url).hostname or ""
    authority = (
        0.2
        if any(
            k in host
            for k in ["folha", "abril", "sesc", "sympla", "eventbrite", "prefeitura"]
        )
        else 0.0
    )

    # short title bonus
    brevity = 0.1 if 20 <= len(title) <= 90 else 0.0

    return weekend * 1.2 + sp * 1.0 + intent * 0.9 + authority + brevity


def dedupe_serp(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for it in items:
        u = it.get("href") or it.get("url") or ""
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(it)
    return out
