from typing import List
from pydantic import BaseModel
from ..llm import LLM


class QueryPlan(BaseModel):
    queries: List[str]


SYSTEM = """
Você é um gerador de consultas de busca.

Gere APENAS consultas de busca para encontrar eventos culturais
EXCLUSIVAMENTE na cidade de São Paulo (SP), Brasil neste fim de semana.

REGRAS OBRIGATÓRIAS:
- TODAS as consultas DEVEM conter explicitamente "São Paulo" ou "SP".
- NÃO inclua Rio de Janeiro, RJ, outras cidades ou estados.
- NÃO inclua termos como mariachi.
- NÃO inclua termos técnicos (json, programação, software).
- NÃO use markdown.
- Responda APENAS com JSON válido.

Formato obrigatório:
{
  "queries": ["consulta 1", "consulta 2", "..."]
}
"""


class Planner:
    def __init__(self, llm: LLM):
        self.llm = llm

    async def plan(self, context: str) -> list[str]:
        plan = await self.llm.json(
            system=SYSTEM,
            user=context,
            schema=QueryPlan,
            max_retries=1,
        )

        # Final safety filter (cheap, defensive)
        clean = []
        seen = set()
        for q in plan.queries:
            q = q.strip()
            if len(q) >= 15 and "json" not in q.lower():
                if q not in seen:
                    seen.add(q)
                    clean.append(q)

        return clean[:8]
