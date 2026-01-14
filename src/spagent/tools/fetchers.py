import re
import httpx
from ..schemas import FetchResult
from bs4 import BeautifulSoup

SYMPLA_URL = "https://www.sympla.com.br/eventos/sao-paulo-sp"
SAO_PAULO_SECRETO_URL = (
    "https://saopaulosecreto.com/o-que-fazer-fim-de-semana-sao-paulo/"
)

HEAD_RE = re.compile(r"<head\b.*?>.*?</head>", re.IGNORECASE | re.DOTALL)
SCRIPT_RE = re.compile(r"<script\b.*?>.*?</script>", re.I | re.S)
STYLE_RE = re.compile(r"<style\b.*?>.*?</style>", re.I | re.S)


def extract_article_body_sao_paulo_secreto(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    section = soup.select_one("section.article__body")

    if not section:
        return html  # fallback

    return section.decode_contents()


async def fetch_sympla_fetcher() -> FetchResult:

    return FetchResult(url=SYMPLA_URL, html="", source="sympla")


async def fetch_sao_paulo_secreto_fetcher() -> FetchResult:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            SAO_PAULO_SECRETO_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        html = r.text
        html = HEAD_RE.sub("", html)
        html = SCRIPT_RE.sub("", html)
        html = STYLE_RE.sub("", html)
        html = extract_article_body_sao_paulo_secreto(html)
        r.raise_for_status()

        return FetchResult(
            url=SAO_PAULO_SECRETO_URL, html=html, source="sao_paulo_secreto"
        )
