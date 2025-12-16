from .planner import Planner
from .actor import Actor
from .evaluator import Evaluator
from .parser import Parser
from ..tools.scraper import scrape_pages
from ..llm import LLM
from ..tools.calendar import current_weekend


class Orchestrator:
    def __init__(self, model: str = "llama3.1:8b-instruct"):
        self.llm = LLM(provider="ollama", model=model)
        self.planner = Planner(self.llm)
        self.actor = Actor()
        self.evaluator = Evaluator()
        self.parser = Parser(self.llm)

    async def weekend_run(self, focus: str = "samba", mode: str = "serp"):
        fri, sun = current_weekend()
        weekend_range = f"{fri.date()} to {sun.date()}"
        queries = self.planner.plan(
            f"Eventos de {fri.date()} a {sun.date()} em São Paulo; foco: {focus}"
        )

        serp = []
        for q in queries:
            serp.extend(self.actor.websearch(q, k=12, timelimit="w"))

        # keep a compact payload
        results = []
        seen = set()
        for r in serp:
            url = r.get("href") or r.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append(
                {
                    "title": r.get("title"),
                    "snippet": r.get("body"),
                    "url": url,
                    "source": r.get("source"),
                    "date": r.get("date"),
                }
            )
            if len(results) >= 30:
                break
        pages = await scrape_pages(r["url"] for r in results)

        url_to_events = {}
        for page in pages:
            events = await self.parser.parse(
                html=page["html"],
                page_url=page["url"],
                weekend_range=weekend_range,
                focus=focus,
            )
            url_to_events[page["url"]] = events

        for r in results:
            r["events_on_page"] = url_to_events.get(r["url"], [])

        score = self.evaluator.score(results)

        return {"queries": queries, "results": results, "score": score.model_dump()}
