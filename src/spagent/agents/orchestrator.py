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
        queries = await self.planner.plan(
            f"Eventos de {fri.date()} a {sun.date()} em São Paulo; foco: {focus}"
        )

        serp = []
        print(
            "================================ QUERIES ===================================\n",
            queries,
        )
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
        print("==================== SERP Results =========================\n", results)
        print("Starting scrapping")
        pages = await scrape_pages(r["url"] for r in results)
        print("==================== SCRAPE RESULTS ==========================\n", pages)
        print("Start parsing")

        url_to_events = {}
        for page in pages:
            events = await self.parser.parse(
                text=page["text"],
                page_url=page["url"],
                weekend_range=weekend_range,
                focus=focus,
            )
            url_to_events[page["url"]] = events
        print(
            "================================ PARSING RESULTS ===================================\n",
            url_to_events,
        )
        for r in results:
            r["events_on_page"] = url_to_events.get(r["url"], [])

        all_events = []
        for r in results:
            evs = r.get("events_on_page") or []
            all_events.extend(evs)

        score = self.evaluator.score(all_events)

        return {"queries": queries, "results": results, "score": score.model_dump()}
