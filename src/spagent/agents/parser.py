from typing import List
from ..llm import LLM
from ..schemas import Event


class Parser:
    def __init__(self, llm: LLM):
        self.llm = llm

    async def parse(
        self, *, text: str, page_url: str, weekend_range: str, focus: str
    ) -> List[Event]:
        if not text:
            return None
        system = """
            You are an information extraction agent.

            Extract events from the provided text.

            Schema:
            [
            {
                "title": string,
                "starts_at": ISO date or null,
                "ends_at": ISO date or null,
                "venue": string or null,
                "city": "São Paulo" or null,
                "category": string or null
            }
            ]
        """

        user = f"""
        DATE_RANGE: {weekend_range}
        FOCUS: {focus}

        TEXT:
        {text}
        """

        return await self.llm.json(system=system, user=user, schema=List[Event])
