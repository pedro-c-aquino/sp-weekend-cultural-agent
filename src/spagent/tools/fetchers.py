import httpx
from ..schemas import FetchResult

SYMPLA_URL = "https://www.sympla.com.br/eventos/sao-paulo-sp"
SAO_PAULO_SECRETO_URL = (
    "https://saopaulosecreto.com/o-que-fazer-fim-de-semana-sao-paulo/"
)


async def fetch_sympla_fetcher() -> FetchResult:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            SYMPLA_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        r.raise_for_status()

        return FetchResult(url=SYMPLA_URL, html=r.text, source="sympla")


async def fetch_sao_paulo_secreto_fetcher() -> FetchResult:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            SAO_PAULO_SECRETO_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        r.raise_for_status()

        return FetchResult(
            url=SAO_PAULO_SECRETO_URL, html=r.text, source="sao_paulo_secreto"
        )
