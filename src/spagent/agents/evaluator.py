from typing import List
from ..llm import LLM
from ..schemas import Evaluation, Event, Result, EvalScore
from . import orchestrator


class Evaluator:
    def __init__(self, llm: LLM):
        self.llm = llm

    async def evaluate(self, results: list[Result]) -> list[Evaluation]:
        print(
            "===========================RESULTS FOR EVALUATION ==============================",
            results,
        )
        if len(results) <= 0:
            return None
        system = """
           You are a evaluator agent.
           Your task is to evaluate if the list returned refers to events happening in São Paulo this weekend. Case they don't you should return false. Case they do, you should return true.
           Schema:
           [
           {
               "title": string,
               "is_event": boolean,
           }
           ]
        """

        user = f"""
        Here is the list for evaluation
        LIST_OF_RESULTS: {results}
        """

        return await self.llm.json(system=system, user=user, schema=List[Evaluation])

    def score(self, events: list[Event]) -> EvalScore:
        # very simple heuristic baseline; replace with LLM-critique later
        fresh = all(e.starts_at is not None for e in events)
        cov = min(1.0, len(events) / 15)
        risk = 0.2 if fresh else 0.6
        return EvalScore(
            coverage=cov,
            freshness_ok=fresh,
            hallucination_risk=risk,
            notes="heuristic v0",
        )
