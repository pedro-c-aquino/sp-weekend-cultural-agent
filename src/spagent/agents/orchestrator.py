from .planner import Planner
from .actor import Actor
from .evaluator import Evaluator
from ..tools.scraper import scrape_pages
from ..llm import LLM
from ..tools.calendar import current_weekend


class Orchestrator:
    def __init__(self, model: str = "llama3.1:8b-instruct"):
        self.llm = LLM(provider="ollama", model=model)
        self.planner = Planner(self.llm)
        self.actor = Actor()
        self.evaluator = Evaluator()

    async def weekend_run(self, focus: str = "samba", mode: str = "serp"):
        fri, sun = current_weekend()
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

        score = self.evaluator.score([])  # evaluator can later inspect snippets
        # if mode == "serp":
        #     return {"queries": queries, "results": results, "score": score.model_dump()}

        # optional crawl enrichment
        urls = [r["url"] for r in results]
        html_events = await scrape_pages(urls, concurrency=6, delay=0.15)
        url_to_events = {}
        for e in html_events:
            url_to_events.setdefault(e["url"], []).append(e)

        merged = []

        for r in results:
            u = r["url"]
            scraped = url_to_events.get(u, [])
            if scraped:
                r["events_on_page"] = scraped
            else:
                r["events_on_page"] = []
            merged.append(r)

        return {
            "queries": queries,
            "results": results,
            "score": score.model_dump(),
        }
