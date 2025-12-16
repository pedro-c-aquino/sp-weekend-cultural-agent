# llm.py
from typing import Type, TypeVar, get_origin, get_args
import json

from pydantic import ValidationError, BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langchain_community.chat_models import ChatOllama
except Exception:  # pragma: no cover
    ChatOllama = None


T = TypeVar("T")


def _extract_json(text: str) -> str:
    """
    Extract JSON from:
    - ```json ... ```
    - ``` ... ```
    - raw JSON
    """
    text = text.strip()

    # Case 1: fenced code block
    if text.startswith("```"):
        lines = text.splitlines()
        # remove first and last fence
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    # Case 2: find first JSON object/array
    for start in ("[", "{"):
        idx = text.find(start)
        if idx != -1:
            return text[idx:].strip()

    return text


class LLM:
    def __init__(self, provider: str = "ollama", model: str = "llama3.1:8b-instruct"):
        self.provider = provider
        self.model = model

        if provider == "ollama":
            if ChatOllama is None:
                raise RuntimeError("LangChain Ollama not installed")
            self.llm = ChatOllama(
                model=model,
                temperature=0.2,
            )
        else:
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(
                model=model,
                temperature=0.2,
            )

    def ask(self, system: str, user: str) -> str:
        msgs = [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
        return self.llm.invoke(msgs).content

    async def json(
        self,
        *,
        system: str,
        user: str,
        schema: Type[T],
        max_retries: int = 1,
    ) -> T:
        """
        Ask the LLM for JSON output and validate against a Pydantic schema.
        """

        json_system = (
            system
            + """

You MUST respond with VALID JSON ONLY.
Do not include markdown, comments, or explanations.
"""
        )

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            raw = self.ask(json_system, user)

            try:
                clean = _extract_json(raw)
                data = json.loads(clean)
                origin = get_origin(schema)
                if origin is list:
                    model = get_args(schema)[0]
                    if not issubclass(model, BaseModel):
                        raise TypeError("List schema must contain BaseModel")
                    return [model.model_validate(x) for x in data]

                # Single BaseModel
                if issubclass(schema, BaseModel):
                    return schema.model_validate(data)

                raise TypeError("Unsupported schema type")

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e

                # Strengthen instruction on retry
                user = f"""
Your previous response was invalid.

ERROR:
{e}

Return ONLY valid JSON that matches the schema.
"""

        raise RuntimeError(
            f"LLM JSON parsing failed after {max_retries + 1} attempts: {last_error}"
        )
