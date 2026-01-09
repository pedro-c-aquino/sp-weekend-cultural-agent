from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama

from ..schemas import Event, EventList, FetchResult

EXTRACTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an information extraction agent.

Your task:
- Extract all real cultural events from the given HTML.
- Ignore navigation, ads, news, unrelated content.
- Do NOT hallucinate missing data.
- If no events exist, return an empty list.

Dates:
- Prefer ISO format YYYY-MM-DD.
- If uncertain, set starts_at = null.

Return ONLY valid JSON that matches this schema:

{{
  "events": [
    {{
      "title": string,
      "starts_at": string | null,
      "ends_at": string | null,
      "date_text": string | null,
      "venue": string | null,
      "city": string | null,
      "category": string | null,
      "price": string | null,
      "link": string | null,
      "source_name": string | null,
      "source_url": string | null
    }}
  ]
}}

IMPORTANT:
- The top-level JSON MUST be an object with a single key "events".
- Do NOT return a raw JSON array.

{format_instructions}
""",
        ),
        ("human", "SOURCE: {source}\nURL: {url}\n\nHTML:\n{html}"),
    ]
)


class ExtractorChain:
    def __init__(self, model: str = "phi3:mini"):
        self.llm = ChatOllama(model=model, temperature=0)

        self.parser = PydanticOutputParser(pydantic_object=EventList)

        self.chain = EXTRACTOR_PROMPT | self.llm | self.parser

    async def extract(self, page: FetchResult) -> EventList:
        html = page.html[:12000]

        raw: EventList = await self.chain.ainvoke(
            {
                "source": page.source,
                "url": page.url,
                "html": html,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        if isinstance(raw, list):
            raw = {"events": raw}

        result = EventList.model_validate(raw)
        events = result.events

        # Inject source metadata defensively
        for e in events:
            e.source_name = page.source
            e.source_url = page.url

        return events
