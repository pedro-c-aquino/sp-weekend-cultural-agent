import json
from pdb import run
from .planner import Planner
from ..llm import LLM
from ..tools.calendar import current_weekend
from .runner import run_agent
from pprint import pprint


class Orchestrator:
    def __init__(self, model: str = "llama3.1:8b-instruct"):
        self.llm = LLM(provider="ollama", model=model)
        self.planner = Planner(self.llm)

    async def weekend_run(self, focus: str, mode: str = "serp"):
        fri, sun = current_weekend()
        weekend_range = f"{fri.date()} to {sun.date()}"
        user_request = f"Eventos de {fri.date()} a {sun.date()} em São Paulo;"

        events, step_results, summary = await run_agent(
            user_request, planner=self.planner
        )

        print(
            "\n============================== EVENTS ================================="
        )
        for i, e in enumerate(events, start=1):
            print(f"\nEvent #{i}")
            pprint(e.model_dump())
