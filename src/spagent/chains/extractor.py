import json
import logging
from pathlib import Path
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

from spagent.utils import normalize_llm_json

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
- NEVER PUT COMMENTS IN THE JSON

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


logger = logging.getLogger(__name__)


class ExtractorChain:
    def __init__(self, model: str = "phi3:mini"):
        self.llm = ChatOllama(model=model, temperature=0)

        self.parser = PydanticOutputParser(pydantic_object=EventList)

        self.chain = EXTRACTOR_PROMPT | self.llm | self.parser

    async def extract(self, page: FetchResult) -> EventList:
        batch_size = 3000

        html = page.html or ""
        print("HTML len = ", len(html))

        # ===== SAVE FULL HTML FOR OFFLINE ANALYSIS =====
        dump_dir = Path("debug_html")
        dump_dir.mkdir(exist_ok=True)

        safe_source = (page.source or "unknown").replace(" ", "_")
        filename = dump_dir / f"{safe_source}.txt"

        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(html)

        print(f"[debug] full HTML saved to {filename.resolve()}")
        # ===============================================

        all_events: List[Event] = []
        batches = [html[i : i + batch_size] for i in range(0, len(html), batch_size)]

        for idx, chunk in enumerate(batches):
            try:
                print(f"Extracting batch {idx + 1} of {len(batches)} from {page.url}")
                result: EventList = await self.chain.ainvoke(
                    {
                        "source": page.source,
                        "url": page.url,
                        "html": chunk,
                        "format_instructions": self.parser.get_format_instructions(),
                    }
                )

                print(
                    "=======================RAW TEXT==========================\n",
                    result,
                )

                events = result.events or []

                # Inject source metadata defensively
                for e in events:
                    e.source_name = page.source
                    e.source_url = page.url

                all_events.extend(events)
            except Exception as e:
                # Don't kill the entire page if one batch fails
                logger.exception(
                    "Extraction failed for batch %s of %s (%s)",
                    idx + 1,
                    len(batches),
                    page.url,
                )
        print(
            "========================ALL EVENTS==========================", all_events
        )
        return EventList(events=all_events)
