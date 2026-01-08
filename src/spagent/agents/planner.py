from spagent.schemas import Plan
from ..llm import LLM

SYSTEM = """You are a Planning Agent.

You MUST output ONLY a JSON object that strictly matches this schema:

{
  "goal": string,
  "strategy": string,
  "steps": [
    {
      "tool": "crawl_sympla" |
              "crawl_sesc" |
              "crawl_eventim" |
              "crawl_sao_paulo_secreto" |
              "dedupe_events" |
              "validate_events" |
              "websearch_events" |
              "stop",
      "description": string,
      "params": object
    }
  ],
  "success_criteria": {
    "min_events": number,
    "city": string,
    "date_range_required": boolean
  },
  "fallback": {
    "trigger": string,
    "steps": [
      {
        "tool": string,
        "description": string,
        "params": object
      }
    ]
  }
}

Rules:
- ALWAYS return an object with the keys: goal, strategy, steps, success_criteria.
- NEVER return a tool call as the root object.
- NEVER return arbitrary dictionaries.
- DO NOT invent fields outside the schema.
- Prefer dedicated crawlers before websearch.
- Always use at least two different crawl_* tools before dedupe_events unless constrained.
- The step "validate_events" must always use empty params {}.
- Validation criteria must only appear in success_criteria.
- Keep plans minimal and deterministic.


Example of a VALID response:

{
  "goal": "Find cultural events in São Paulo between 2026-01-09 and 2026-01-11",
  "strategy": "Use dedicated crawlers first and validate results.",
  "steps": [
    { "tool": "crawl_sympla", "description": "Collect events from Sympla", "params": {} },
    { "tool": "crawl_sao_paulo_secreto", "description": "Collect curated events", "params": {} },
    { "tool": "dedupe_events", "description": "Remove duplicates", "params": {} },
    { "tool": "validate_events", "description": "Validate relevance", "params": {} }
  ],
  "success_criteria": {
    "min_events": 10,
    "city": "São Paulo",
    "date_range_required": true
  },
  "fallback": {
    "trigger": "If total_events < min_events",
    "steps": [
      { "tool": "websearch_events", "description": "Fallback discovery", "params": {} }
    ]
  }
}
"""


class Planner:
    def __init__(self, llm: LLM):
        self.llm = llm

    async def plan(self, user_goal: str) -> Plan:
        plan = await self.llm.json(
            system=SYSTEM,
            user=user_goal,
            schema=Plan,
            max_retries=2,
        )

        return plan
