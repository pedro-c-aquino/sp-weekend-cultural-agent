from ..schemas import Event, EvalScore
from . import orchestrator


class Evaluator:
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
