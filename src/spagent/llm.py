# llm.py
from typing import Type, TypeVar, get_origin, get_args
import json
import re

from pydantic import ValidationError, BaseModel
from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langchain_community.chat_models import ChatOllama
except Exception:  # pragma: no cover
    ChatOllama = None


T = TypeVar("T")


def _extract_json(text: str) -> str:
    """
    Extract the first valid JSON object or array from text
    by matching balanced braces/brackets.
    """
    text = text.strip()

    # Remove code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = None
    stack = []
    for i, ch in enumerate(text):
        if ch in "{[":
            if start is None:
                start = i
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue
            opening = stack.pop()
            if not stack:
                # Found matching end
                return text[start : i + 1]

    return text  # fallback (will fail loudly)


def _autoclose_json(text: str) -> str:
    """
    Close unbalanced JSON braces/brackets.
    Last-resort repair for truncated outputs.
    """
    text = text.rstrip()

    open_curly = text.count("{")
    close_curly = text.count("}")
    open_square = text.count("[")
    close_square = text.count("]")

    if close_curly < open_curly:
        text += "}" * (open_curly - close_curly)
    if close_square < open_square:
        text += "]" * (open_square - close_square)

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

STRICT RULES:
- Return ONLY valid JSON.
- Do NOT use markdown or code fences.
- Return at most 5 items.
- Always close all JSON objects and arrays.
- If unsure, return an empty array [].
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

                try:
                    repaired = _autoclose_json(clean)
                    data = json.loads(repaired)
                    origin = get_origin(schema)
                    if origin is list:
                        model = get_args(schema)[0]
                        return [model.model_validate(x) for x in data]
                    if issubclass(schema, BaseModel):
                        return schema.model_validate(data)
                except Exception:
                    pass

                # Repair-only retry prompt
                user = f"""
            The JSON below is INVALID.

            Fix it.
            Do NOT add new items.
            Do NOT remove existing items.
            Do NOT use markdown.
            Return ONLY valid JSON.

            INVALID JSON:
            {clean}
            """

        raise RuntimeError(
            f"LLM JSON parsing failed after {max_retries + 1} attempts: {last_error}"
        )
