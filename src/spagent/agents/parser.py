from typing import List
from ..llm import LLM
from ..schemas import Event


class Parser:
    def __init__(self, llm: LLM):
        self.llm = llm

    async def parse(
        self, *, html: str, page_url: str, weekend_range: str, focus: str
    ) -> List[Event]:
        if not html:
            return None
        system = """
                You are an information extraction agent.

                Your task:
                - Extract REAL EVENTS from the provided HTML.
                - Events must be happening in São Paulo city.
                - Events must fall within the given date range.
                - If the page does NOT list events, return an empty list.
                - NEVER invent events.
                - NEVER infer missing dates or locations.
                - Use only what is explicitly stated in the HTML.

                Return JSON ONLY, following the provided schema.

                Each event MUST use EXACTLY these fields:
                - title (string, required)
                - starts_at (ISO-8601 datetime string or null)
                - ends_at (ISO-8601 datetime string or null)
                - date_text (string or null)
                - venue (string or null)
                - city (string or null)
                - category (string or null)
                - price (string or null)
                - link (string or null)
                - source_name (string or null)
                - source_url (string or null)

                Rules:
                - Use null if unknown
                - Do not invent dates
                - Do not invent venues
                - City must be "São Paulo" if explicitly mentioned
        """

        user = f"""
        DATE_RANGE: {weekend_range}

        FOCUS:
        {focus}

        PAGE URL:
        {page_url}

        HTML:
        ```html
        {html[:120_000]}
        """

        return await self.llm.json(system=system, user=user, schema=List[Event])
