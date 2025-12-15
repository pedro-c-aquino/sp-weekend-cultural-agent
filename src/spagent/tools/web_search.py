from duckduckgo_search import DDGS
from typing import List, Dict, Optional


class WebSearch:
    def __init__(self, region="br-pt", safesearch="moderate"):
        self.region = region
        self.safesearch = safesearch

    def search(
        self, query: str, max_results: int = 12, timelimit: Optional[str] = "w"
    ) -> List[Dict]:
        """
        timelimit: None|'d'|'w'|'m'|'y' (last day/week/month/year)
        Returns: [{title, href, body, source, date, ...}]
        """
        with DDGS() as ddgs:
            return list(
                ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    max_results=max_results,
                    timelimit=timelimit,
                )
            )
