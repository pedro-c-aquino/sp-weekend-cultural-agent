from ..llm import LLM


SYSTEM = (
    "Você é o Planner. Sua tarefa é gerar apenas consultas de busca para São Paulo no fim de semana."
    " Responda **exatamente** com um JSON válido no formato:\n"
    ' {"queries": ["<consulta 1>", "<consulta 2>", "..."]} \n'
    "Regras:\n"
    "- Não use blocos de código (sem ```json). \n"
    "- Não inclua objetos aninhados, nem strings contendo JSON. Somente strings simples. \n"
    "- 5 a 8 consultas, em PT-BR, focadas em agenda cultural (shows, teatro, samba, etc.)."
)


PROMPT = (
    "Gere 5 a 8 consultas diferentes que uma pessoa digitaria no Google "
    "para encontrar eventos, peças, shows e exposições em São Paulo neste fim de semana. "
    "Evite falar de outras cidades. Use termos como 'agenda', 'programação', 'shows', 'samba', 'teatro'. "
    "Não gere queries sobre json ou sobre programação relativa à tecnologia da informação, apenas sobre agenda de eventos "
    "Responda apenas com JSON válido."
)


class Planner:
    def __init__(self, llm: LLM):
        self.llm = llm

    def _strip_code_fences(self, text: str) -> str:
        import re

        t = text.strip()
        # remove leading/trailing ``` or ```json fences
        t = re.sub(r"^\s*```(?:json)?\s*", "", t, flags=re.S)
        t = re.sub(r"\s*```\s*$", "", t, flags=re.S)
        return t.strip()

    def _normalize_item(self, item) -> str | None:
        """
        Accepts either a plain string or a dict-like query.
        Returns a plain string or None if cannot normalize.
        """
        import json

        if isinstance(item, str):
            s = item.strip().rstrip(",")
            # If model put a JSON object as a *string*, try to parse and extract.
            if s.startswith("{") and s.endswith("}"):
                try:
                    obj = json.loads(s)
                    return self._normalize_item(obj)
                except Exception:
                    return s if len(s) > 5 else None
            return s if len(s) > 5 else None

        if isinstance(item, dict):
            # Prefer explicit 'query'
            q = item.get("query")
            if isinstance(q, str) and len(q.strip()) > 5:
                return q.strip()

            # Otherwise, synthesize a human query from fields.
            parts = []
            # eventType / keywords can be lists
            et = item.get("eventType")
            if isinstance(et, list) and et:
                parts.append(" ".join(et))
            kw = item.get("keywords")
            if isinstance(kw, list) and kw:
                parts.append(" ".join(kw))
            loc = item.get("location")
            if isinstance(loc, str):
                parts.append(loc)
            sd = item.get("startDate")
            ed = item.get("endDate")
            if sd or ed:
                if sd and ed:
                    parts.append(f"{sd} a {ed}")
                else:
                    parts.append(sd or ed)
            # Fallback label
            if parts:
                return " ".join(parts).strip()
            return None

        return None

    def plan(self, query: str) -> list[str]:
        out = self.llm.ask(SYSTEM, f"{PROMPT}\n\nSolicitação: {query}")
        # simple JSON fallback
        candidate = self._strip_code_fences(out)
        data = None
        import json, re

        try:
            data = json.loads(candidate)

        except Exception:
            m = re.search(r"\{.*\}", candidate, flags=re.S)
            if m:
                try:
                    data = json.loads(m.group(0))
                except Exception:
                    data = None

        queries: list[str] = []

        if (
            isinstance(data, dict)
            and "queries" in data
            and isinstance(data["queries"], list)
        ):
            for item in data["queries"]:
                q = self._normalize_item(item)
                if q:
                    queries.append(q)
        else:
            # very naive fallback: pick meaningful non-empty lines
            lines = [l.strip("- •\t ,") for l in out.splitlines() if l.strip()]
            queries = [l for l in lines if len(l) > 5][:6]

        # 3) final cleanup: dedupe + drop any leftover fence-y bits
        seen = set()
        clean = []
        for q in queries:
            q = q.replace("```", "").strip().strip(",")
            if q and q not in seen:
                seen.add(q)
                clean.append(q)

        # Optional: print for debugging
        return clean
